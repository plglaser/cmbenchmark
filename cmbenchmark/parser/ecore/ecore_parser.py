"""Ecore parser for converting Ecore models to graph-based IR."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
import uuid

try:
    from pyecore.resources import ResourceSet, URI
    from pyecore.ecore import (
        EAnnotation,
        EAttribute,
        EClass,
        EDataType,
        EEnum,
        EEnumLiteral,
        EProxy,
        EModelElement,
        ENamedElement,
        EObject,
        EOperation,
        EPackage,
        EParameter,
        EReference,
        EStructuralFeature,
        ETypedElement,
    )
except ImportError:
    raise ImportError(
        "pyecore is required for Ecore parsing. Install it with: pip install pyecore"
    )

from cmbenchmark.parser.base import BaseParser, register_parser
from cmbenchmark.types.enums import WarningType
from cmbenchmark.types.exceptions import CannotParseError
from cmbenchmark.types.ir import Edge, IR, Node
from cmbenchmark.types.parsing import ParserRunStats


def _generate_id(prefix: str = "") -> str:
    """Generate a unique ID for nodes/edges."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}" if prefix else uuid.uuid4().hex[:8]


def _safe_bool(value: Optional[bool], default: bool) -> bool:
    return default if value is None else bool(value)


def _safe_int(value: Optional[int], default: int) -> int:
    return default if value is None else int(value)


@dataclass(frozen=True)
class ExternalDataTypeRef:
    """Synthetic key for external datatypes that pyecore doesn't resolve to EObjects (e.g. EString)."""

    nsURI: str
    packageName: str
    name: str


@dataclass(frozen=True)
class ExternalClassRef:
    """Synthetic key for external classes that pyecore doesn't resolve to EObjects (e.g. EObject)."""

    nsURI: str
    packageName: str
    name: str
    originResource: str = ""


@register_parser
class EcoreParser(BaseParser):
    """Parser for Ecore metamodels."""

    language = "Ecore"

    def parse(self, filepath: str) -> Tuple[IR, ParserRunStats]:
        """
        Parse an Ecore model file into IR.

        Args:
            filepath: Path to the .ecore file

        Returns:
            Tuple of (IR object, ParserRunStats)

        Raises:
            CannotParseError: If the file is not a valid Ecore model
        """
        self._start_run()

        path = Path(filepath)
        if not path.exists():
            raise CannotParseError(f"File does not exist: {filepath}")

        try:
            rset = ResourceSet()
            resource = rset.create_resource(URI(str(path.absolute())))
            try:
                resource.load()
            except TypeError as e:
                # pyecore raises TypeError when an externally referenced resource can't be resolved.
                # We still want to proceed with a partially loaded model and keep the reference
                # as an EProxy so we can materialize a stub node.
                msg = str(e)
                if "cannot be resolved problem with" in msg:
                    self.warn(
                        WarningType.UNRESOLVED_REFERENCE,
                        f"External resource could not be resolved while loading '{filepath}': {msg}",
                    )
                else:
                    raise

            if not resource.contents:
                raise CannotParseError("Ecore file appears to be empty")

            mm_roots = self._detect_root_packages(resource.contents)

            # Register all root packages (best-effort) so cross-resource resolution can work
            for pkg in mm_roots:
                if pkg.nsURI:
                    rset.metamodel_registry[pkg.nsURI] = pkg

        except Exception as e:
            if isinstance(e, CannotParseError):
                raise
            raise CannotParseError(f"Failed to load Ecore model: {e}")

        primary_root = mm_roots[0]
        root_packages_meta = [
            {"name": pkg.name or "", "nsURI": pkg.nsURI or "", "nsPrefix": pkg.nsPrefix or ""}
            for pkg in mm_roots
        ]
        ir = IR(
            id=_generate_id("model"),
            language=self.language,
            data={
                "path": str(path.absolute()),
                "rootPackages": root_packages_meta,
                "rootPackageCount": len(mm_roots),
                "hasMultipleRootPackages": len(mm_roots) > 1,
            },
        )
        self._add_model_level_annotations(resource.contents, ir.data)

        # Collect all EObjects across all root packages (stable order, de-duplicated)
        all_eobjects: List[EObject] = []
        seen: set = set()
        for root in mm_roots:
            for obj in [root] + list(root.eAllContents()):
                if obj in seen:
                    continue
                seen.add(obj)
                all_eobjects.append(obj)

        node_eobjects: List[Union[EObject, ExternalDataTypeRef]] = self._filter_node_eobjects(
            all_eobjects
        )
        node_eobjects = self._extend_with_referenced_datatypes(node_eobjects, all_eobjects)
        node_eobjects = self._extend_with_referenced_external_classes(node_eobjects, all_eobjects)
        eobject_to_id = self._build_eobject_index(node_eobjects)

        for eobj in node_eobjects:
            node = self._build_node(eobj, eobject_to_id, root_pkgs=mm_roots)
            if node is not None:
                ir.nodes.append(node)

        ir.edges.extend(self._build_edges(all_eobjects, eobject_to_id))

        return ir, self._stats()

    def _detect_root_packages(self, contents: Iterable[Any]) -> List[EPackage]:
        """
        Root detection:
        - Scan resource.contents for EPackage objects.
        - 0 packages: hard parse error
        - >=1 package: parse all of them (multi-root Ecore resources are common)
        """
        packages = [obj for obj in contents if isinstance(obj, EPackage)]
        if len(packages) == 0:
            raise CannotParseError("No EPackage found in resource")
        return packages

    def _add_model_level_annotations(self, contents: Iterable[Any], model_data: Dict[str, Any]) -> None:
        """
        Collect top-level EAnnotations (directly under resource.contents) into IR.data.
        """
        annotations = [obj for obj in contents if isinstance(obj, EAnnotation)]
        if not annotations:
            return
        model_ann: Dict[str, Dict[str, str]] = model_data.setdefault("modelAnnotations", {})
        for ann in annotations:
            source = ann.source or ""
            block = model_ann.setdefault(source, {})
            # include nested annotations as well
            stack = [ann]
            while stack:
                current = stack.pop()
                for key, value in self._iter_annotation_details(current):
                    block[str(key)] = str(value)
                if isinstance(current, EModelElement) and current.eAnnotations:
                    stack.extend(list(current.eAnnotations))

    def _filter_node_eobjects(self, eobjects: Iterable[EObject]) -> List[EObject]:
        node_types = (
            EPackage,
            EClass,
            EDataType,
            EEnum,
            EEnumLiteral,
            EAttribute,
            EOperation,
            EParameter,
        )
        return [obj for obj in eobjects if isinstance(obj, node_types)]

    def _extend_with_referenced_datatypes(
        self,
        node_eobjects: List[Union[EObject, ExternalDataTypeRef]],
        all_eobjects: Iterable[EObject],
    ) -> List[Union[EObject, ExternalDataTypeRef]]:
        """
        Ensure that all non-enum EDataTypes referenced via eType are materialized as nodes.

        This includes external Ecore primitives like EString/EBoolean/EFloat.
        """
        existing = set(node_eobjects)
        extra: List[Union[EObject, ExternalDataTypeRef]] = []

        for obj in all_eobjects:
            if isinstance(obj, (EAttribute, EOperation, EParameter)):
                raw_etype = getattr(obj, "eType", None)
                if raw_etype is None:
                    continue
                etype = self._normalize_etype(raw_etype)
                if etype is None:
                    continue
                if isinstance(etype, EEnum):
                    continue  # already handled as normal node via eAllContents
                if isinstance(etype, EDataType) or isinstance(etype, ExternalDataTypeRef):
                    if etype not in existing:
                        existing.add(etype)
                        extra.append(etype)

        return node_eobjects + extra

    def _extend_with_referenced_external_classes(
        self,
        node_eobjects: List[Union[EObject, ExternalDataTypeRef, ExternalClassRef]],
        all_eobjects: Iterable[EObject],
    ) -> List[Union[EObject, ExternalDataTypeRef, ExternalClassRef]]:
        """
        Ensure that external EClasses referenced via EReference.eType are materialized as nodes.

        Common case: EObject from Ecore package.
        """
        existing = set(node_eobjects)
        extra: List[Union[EObject, ExternalDataTypeRef, ExternalClassRef]] = []

        for obj in all_eobjects:
            # External EClass reference targets
            if isinstance(obj, EReference):
                raw_target = getattr(obj, "eType", None)
                ext = self._normalize_external_eclass(raw_target)
                if ext is not None and ext not in existing:
                    existing.add(ext)
                    extra.append(ext)
            # External superclasses
            if isinstance(obj, EClass):
                for st in obj.eSuperTypes:
                    ext = self._normalize_external_eclass(st)
                    if ext is not None and ext not in existing:
                        existing.add(ext)
                        extra.append(ext)

        return list(node_eobjects) + extra

    def _build_eobject_index(
        self, eobjects: Iterable[Union[EObject, ExternalDataTypeRef, ExternalClassRef]]
    ) -> Dict[Any, str]:
        eobject_to_id: Dict[Any, str] = {}
        for index, obj in enumerate(eobjects, start=1):
            if obj in eobject_to_id:
                self.skip_with_warning(
                    WarningType.DUPLICATE_ID,
                    f"Duplicate EObject encountered: {obj}",
                )
                continue
            if isinstance(obj, (ExternalDataTypeRef, ExternalClassRef)):
                node_type = "EDataType"
                if isinstance(obj, ExternalClassRef):
                    node_type = "EClass"
            else:
                node_type = obj.eClass.name if hasattr(obj, "eClass") else type(obj).__name__
            eobject_to_id[obj] = f"{node_type}_{index}"
        return eobject_to_id

    def _build_node(
        self,
        obj: Union[EObject, ExternalDataTypeRef, ExternalClassRef],
        eobject_to_id: Dict[Any, str],
        root_pkgs: List[EPackage],
    ) -> Optional[Node]:
        node_id = eobject_to_id.get(obj)
        if not node_id:
            self.skip_with_warning(
                WarningType.UNRESOLVED_REFERENCE,
                f"Missing node id for EObject: {obj}",
            )
            return None

        if isinstance(obj, ExternalDataTypeRef):
            return Node(
                id=node_id,
                type="EDataType",
                name=obj.name,
                data={
                    "external": True,
                    "nsURI": obj.nsURI,
                    "packageName": obj.packageName,
                },
            )
        if isinstance(obj, ExternalClassRef):
            return Node(
                id=node_id,
                type="EClass",
                name=obj.name,
                data={
                    "external": True,
                    **({"nsURI": obj.nsURI} if obj.nsURI else {}),
                    **({"packageName": obj.packageName} if obj.packageName else {}),
                    **({"originResource": obj.originResource} if obj.originResource else {}),
                },
            )

        node_type = obj.eClass.name if hasattr(obj, "eClass") else type(obj).__name__
        name = obj.name if isinstance(obj, ENamedElement) and obj.name else ""
        data: Dict[str, Any] = {}

        if isinstance(obj, EPackage):
            data["nsURI"] = obj.nsURI or ""
            data["nsPrefix"] = obj.nsPrefix or ""
        elif isinstance(obj, EClass):
            data["abstract"] = bool(obj.abstract)
            data["interface"] = bool(obj.interface)
        elif isinstance(obj, EEnum):
            pass
        elif isinstance(obj, EDataType):
            self._fill_datatype_data(obj, data, root_pkgs=root_pkgs)
        elif isinstance(obj, EEnumLiteral):
            pass
        elif isinstance(obj, EAttribute):
            self._fill_typed_element_data(obj, data)
            self._fill_structural_feature_data(obj, data)
            data["iD"] = bool(obj.iD)
        elif isinstance(obj, EOperation):
            self._fill_typed_element_data(obj, data)
            data["throws"] = [
                ex.name if isinstance(ex, ENamedElement) and ex.name else ""
                for ex in obj.eExceptions
            ]
        elif isinstance(obj, EParameter):
            self._fill_typed_element_data(obj, data)

        self._fill_annotation_data(obj, data, recursive=True)

        return Node(id=node_id, type=node_type, name=name, data=data)

    def _normalize_etype(self, raw_etype: Any) -> Optional[Union[EObject, ExternalDataTypeRef]]:
        """
        Normalize ETypedElement.eType into either a real EObject (preferred) or a synthetic
        ExternalDataTypeRef when pyecore leaves builtins as strings.
        """
        if raw_etype is None:
            return None
        if isinstance(raw_etype, EProxy):
            proxy_path = getattr(raw_etype, "_proxy_path", "") or ""
            ref = self._parse_proxy_datatype_ref(proxy_path)
            if ref is None:
                self.skip_with_warning(
                    WarningType.UNRESOLVED_REFERENCE,
                    f"Could not resolve proxy eType: {proxy_path!r}",
                )
            return ref
        if isinstance(raw_etype, EObject):
            return raw_etype
        if isinstance(raw_etype, str):
            ref = self._parse_external_datatype_ref(raw_etype)
            if ref is None:
                self.skip_with_warning(
                    WarningType.UNRESOLVED_REFERENCE,
                    f"Could not parse eType reference: {raw_etype!r}",
                )
            return ref
        return None

    def _parse_external_datatype_ref(self, etype_str: str) -> Optional[ExternalDataTypeRef]:
        """
        Parse strings like:
          'ecore:EDataType http://www.eclipse.org/emf/2002/Ecore#//EString'
        into ExternalDataTypeRef(nsURI='http://www.eclipse.org/emf/2002/Ecore',
                                 packageName='ecore', name='EString').
        """
        parts = etype_str.strip().split()
        if not parts:
            return None

        # Common XMI form: "<prefix>:EDataType <nsURI>#//<Name>"
        prefix_part = parts[0]
        uri_part = parts[1] if len(parts) > 1 else ""
        package_name = prefix_part.split(":")[0] if ":" in prefix_part else ""

        ns_uri = uri_part.split("#", 1)[0] if "#" in uri_part else uri_part
        name = ""
        if "#//" in uri_part:
            name = uri_part.split("#//", 1)[1]
        elif uri_part:
            name = uri_part.rsplit("/", 1)[-1]

        if not name:
            return None
        if not ns_uri:
            ns_uri = "http://www.eclipse.org/emf/2002/Ecore"
        if not package_name:
            package_name = "ecore"

        return ExternalDataTypeRef(nsURI=ns_uri, packageName=package_name, name=name)

    def _parse_proxy_datatype_ref(self, proxy_path: str) -> Optional[ExternalDataTypeRef]:
        """
        Parse EProxy paths like:
          'http://www.eclipse.org/emf/2002/Ecore#//EString'
        """
        proxy_path = (proxy_path or "").strip()
        if not proxy_path:
            return None
        ns_uri = proxy_path.split("#", 1)[0] if "#" in proxy_path else ""
        name = proxy_path.split("#//", 1)[1] if "#//" in proxy_path else ""
        if not name:
            return None
        if not ns_uri:
            ns_uri = "http://www.eclipse.org/emf/2002/Ecore"
        # Best-effort package name: Ecore's is conventionally "ecore"
        package_name = "ecore" if "emf/2002/Ecore" in ns_uri else ""
        return ExternalDataTypeRef(nsURI=ns_uri, packageName=package_name or "ecore", name=name)

    def _normalize_external_eclass(self, raw_etype: Any) -> Optional[ExternalClassRef]:
        """
        For EReference.eType we want an EClass target node.
        If the type is unresolved and represented as proxy or string, create an external EClass ref.
        """
        if raw_etype is None:
            return None
        if isinstance(raw_etype, EProxy):
            proxy_path = getattr(raw_etype, "_proxy_path", "") or ""
            return self._parse_proxy_eclass_ref(proxy_path)
        if isinstance(raw_etype, str):
            # Handle 'ecore:EClass http://...#//EObject'
            return self._parse_external_eclass_ref(raw_etype)
        return None

    def _parse_proxy_eclass_ref(self, proxy_path: str) -> Optional[ExternalClassRef]:
        proxy_path = (proxy_path or "").strip()
        if not proxy_path:
            return None
        ns_uri = proxy_path.split("#", 1)[0] if "#" in proxy_path else ""
        name = proxy_path.split("#//", 1)[1] if "#//" in proxy_path else ""
        if not name:
            return None
        # Case 1: standard Ecore URL
        if ns_uri.startswith("http://") or ns_uri.startswith("https://"):
            package_name = "ecore" if "emf/2002/Ecore" in ns_uri else ""
            return ExternalClassRef(
                nsURI=ns_uri or "http://www.eclipse.org/emf/2002/Ecore",
                packageName=package_name or "ecore",
                name=name,
            )
        # Case 2: relative resource reference like "external.ecore#//E"
        origin = ns_uri
        return ExternalClassRef(nsURI="", packageName="", name=name, originResource=origin)

    def _parse_external_eclass_ref(self, etype_str: str) -> Optional[ExternalClassRef]:
        """
        Parse strings like:
          'ecore:EClass http://www.eclipse.org/emf/2002/Ecore#//EObject'
        """
        parts = etype_str.strip().split()
        if len(parts) < 2:
            return None
        prefix_part = parts[0]
        uri_part = parts[1]
        package_name = prefix_part.split(":")[0] if ":" in prefix_part else "ecore"
        ns_uri = uri_part.split("#", 1)[0] if "#" in uri_part else uri_part
        name = uri_part.split("#//", 1)[1] if "#//" in uri_part else ""
        if not name:
            return None
        if not ns_uri:
            ns_uri = "http://www.eclipse.org/emf/2002/Ecore"
        return ExternalClassRef(nsURI=ns_uri, packageName=package_name or "ecore", name=name)

    def _fill_typed_element_data(self, obj: ETypedElement, data: Dict[str, Any]) -> None:
        data["ordered"] = _safe_bool(getattr(obj, "ordered", None), True)
        data["unique"] = _safe_bool(getattr(obj, "unique", None), True)
        data["lowerBound"] = _safe_int(getattr(obj, "lowerBound", None), 0)
        data["upperBound"] = _safe_int(getattr(obj, "upperBound", None), 1)
        data["required"] = data["lowerBound"] >= 1

    def _fill_structural_feature_data(
        self, obj: EStructuralFeature, data: Dict[str, Any]
    ) -> None:
        data["changeable"] = _safe_bool(getattr(obj, "changeable", None), True)
        data["volatile"] = _safe_bool(getattr(obj, "volatile", None), False)
        data["transient"] = _safe_bool(getattr(obj, "transient", None), False)
        data["unsettable"] = _safe_bool(getattr(obj, "unsettable", None), False)
        data["derived"] = _safe_bool(getattr(obj, "derived", None), False)

    def _fill_annotation_data(
        self, obj: EObject, data: Dict[str, Any], recursive: bool = False
    ) -> None:
        if not isinstance(obj, EModelElement):
            return
        if not obj.eAnnotations:
            return
        annotations: Dict[str, Dict[str, str]] = data.setdefault("annotations", {})
        if not recursive:
            for ann in obj.eAnnotations:
                source = ann.source or ""
                source_block = annotations.setdefault(source, {})
                for key, value in self._iter_annotation_details(ann):
                    source_block[str(key)] = str(value)
            return

        stack = list(obj.eAnnotations)
        while stack:
            ann = stack.pop()
            source = ann.source or ""
            source_block = annotations.setdefault(source, {})
            for key, value in self._iter_annotation_details(ann):
                source_block[str(key)] = str(value)
            if isinstance(ann, EModelElement) and ann.eAnnotations:
                stack.extend(list(ann.eAnnotations))

    def _fill_datatype_data(
        self, dtype: EDataType, data: Dict[str, Any], root_pkgs: List[EPackage]
    ) -> None:
        """
        Minimal but informative EDataType payload, with internal/external classification.
        """
        pkg = getattr(dtype, "ePackage", None)
        internal = bool(pkg) and self._is_package_within_any_root(pkg, root_pkgs)
        data["external"] = not internal
        if not internal:
            data["nsURI"] = (pkg.nsURI if pkg is not None and pkg.nsURI else "http://www.eclipse.org/emf/2002/Ecore")
            data["packageName"] = (pkg.name if pkg is not None and pkg.name else "ecore")

    def _is_package_within_any_root(self, pkg: EPackage, root_pkgs: Iterable[EPackage]) -> bool:
        """
        Returns True iff pkg is within any of the root packages (including the roots themselves).
        """
        root_set = set(root_pkgs)
        current: Optional[EPackage] = pkg
        while current is not None:
            if current in root_set:
                return True
            current = getattr(current, "eSuperPackage", None)
        return False

    def _iter_annotation_details(
        self, ann: EAnnotation
    ) -> Iterable[Tuple[str, str]]:
        details = getattr(ann, "details", None)
        if details is None:
            return []
        if hasattr(details, "items"):
            return list(details.items())
        entries = []
        for entry in details:
            key = getattr(entry, "key", None)
            value = getattr(entry, "value", None)
            if key is not None:
                entries.append((key, value))
        return entries

    def _build_edges(
        self, all_eobjects: Iterable[EObject], eobject_to_id: Dict[Any, str]
    ) -> List[Edge]:
        edges: List[Edge] = []
        created_keys: set = set()
        edge_counter = 0

        def add_edge(
            edge_type: str,
            source: EObject,
            target: Any,
            data: Dict[str, Any],
            key_hint: Tuple[Any, ...],
        ) -> None:
            nonlocal edge_counter
            source_id = eobject_to_id.get(source)
            target_id = eobject_to_id.get(target)
            if not source_id or not target_id:
                self.skip_with_warning(
                    WarningType.UNRESOLVED_REFERENCE,
                    f"Unresolved edge {edge_type} from {source} to {target}",
                )
                return
            edge_key = (edge_type, source_id, target_id) + key_hint
            if edge_key in created_keys:
                self.skip_with_warning(
                    WarningType.DUPLICATE_ID,
                    f"Duplicate edge {edge_type} from {source_id} to {target_id}",
                )
                return
            created_keys.add(edge_key)
            edge_id = _generate_id(f"edge_{edge_counter}")
            edge_counter += 1
            edges.append(
                Edge(
                    id=edge_id,
                    sourceId=source_id,
                    targetId=target_id,
                    type=edge_type,
                    data=data,
                )
            )

        for obj in all_eobjects:
            if isinstance(obj, EPackage):
                for sub in obj.eSubpackages:
                    add_edge(
                        "Contains",
                        obj,
                        sub,
                        {"feature": "eSubpackages"},
                        ("eSubpackages",),
                    )
                for classifier in obj.eClassifiers:
                    add_edge(
                        "Contains",
                        obj,
                        classifier,
                        {"feature": "eClassifiers"},
                        ("eClassifiers",),
                    )
            elif isinstance(obj, EClass):
                for attr in obj.eAttributes:
                    add_edge(
                        "Contains",
                        obj,
                        attr,
                        {"feature": "eStructuralFeatures", "kind": "EAttribute"},
                        ("eStructuralFeatures", "EAttribute"),
                    )
                for op in obj.eOperations:
                    add_edge(
                        "Contains",
                        obj,
                        op,
                        {"feature": "eOperations"},
                        ("eOperations",),
                    )
                for super_class in obj.eSuperTypes:
                    target = self._normalize_external_eclass(super_class) or super_class
                    add_edge(
                        "Generalization",
                        obj,
                        target,
                        {"feature": "eSuperTypes"},
                        ("eSuperTypes",),
                    )
                for ref in obj.eReferences:
                    self._add_reference_edge(ref, eobject_to_id, add_edge)
            elif isinstance(obj, EEnum):
                for lit in obj.eLiterals:
                    add_edge(
                        "Contains",
                        obj,
                        lit,
                        {"feature": "eLiterals"},
                        ("eLiterals",),
                    )
            elif isinstance(obj, EOperation):
                for param in obj.eParameters:
                    add_edge(
                        "Contains",
                        obj,
                        param,
                        {"feature": "eParameters"},
                        ("eParameters",),
                    )

            if isinstance(obj, EAttribute):
                if obj.eType is not None:
                    target = self._normalize_etype(obj.eType)
                    if target is None:
                        continue
                    add_edge(
                        "AttributeType",
                        obj,
                        target,
                        {"feature": "eType", "kind": "attributeType"},
                        ("eType", "attributeType"),
                    )
            elif isinstance(obj, EOperation):
                if obj.eType is not None:
                    target = self._normalize_etype(obj.eType)
                    if target is None:
                        continue
                    add_edge(
                        "Type",
                        obj,
                        target,
                        {"feature": "eType", "kind": "return"},
                        ("eType", "return"),
                    )
            elif isinstance(obj, EParameter):
                if obj.eType is not None:
                    target = self._normalize_etype(obj.eType)
                    if target is None:
                        continue
                    add_edge(
                        "Type",
                        obj,
                        target,
                        {"feature": "eType", "kind": "parameter"},
                        ("eType", "parameter"),
                    )

        return edges

    def _add_reference_edge(
        self,
        ref: EReference,
        eobject_to_id: Dict[Any, str],
        add_edge,
    ) -> None:
        source = ref.eContainingClass
        target = ref.eType
        if source is None or target is None:
            self.skip_with_warning(
                WarningType.UNRESOLVED_REFERENCE,
                f"Reference missing source or target: {ref}",
            )
            return
        normalized_target = self._normalize_external_eclass(target)
        if normalized_target is not None:
            target = normalized_target

        data: Dict[str, Any] = {
            "name": ref.name or "",
            "ordered": _safe_bool(getattr(ref, "ordered", None), True),
            "unique": _safe_bool(getattr(ref, "unique", None), True),
            "lowerBound": _safe_int(getattr(ref, "lowerBound", None), 0),
            "upperBound": _safe_int(getattr(ref, "upperBound", None), 1),
            "required": _safe_int(getattr(ref, "lowerBound", None), 0) >= 1,
            "changeable": _safe_bool(getattr(ref, "changeable", None), True),
            "volatile": _safe_bool(getattr(ref, "volatile", None), False),
            "transient": _safe_bool(getattr(ref, "transient", None), False),
            "unsettable": _safe_bool(getattr(ref, "unsettable", None), False),
            "derived": _safe_bool(getattr(ref, "derived", None), False),
            "containment": bool(ref.containment),
            "container": bool(ref.container),
        }

        self._fill_annotation_data(ref, data, recursive=True)

        if ref.eOpposite is not None:
            data["oppositeName"] = ref.eOpposite.name or ""
            data["hasOpposite"] = True

        edge_type = "Containment" if ref.containment else "Reference"
        add_edge(edge_type, source, target, data, ("eReferences", ref.name or ""))
