from pyecore.resources import ResourceSet, URI

try:
    rset = ResourceSet()
    resource = rset.create_resource(URI("/Users/philipp/Projects/CM-Benchmarking/cmbenchmark/data/AtlantEcore/mlhim2.ecore"))
    resource.load()
except TypeError as e:
    print(e)

print(resource.contents)