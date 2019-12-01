"""
1. Nim Compiler Invoker
2. Nim Import Hook
3. Nim Build Artifact Cacher
	Compile and then store in __pycache__
"""

import sys, subprocess

def nim_compile(file_path):
	ext = '.pyd' if sys.platform == 'win32' else '.so'
	build_artifact = file_path.parent / "__pycache__" / (file_path.stem + ext)
	cmd = (
		f'nim c --threads:on --tlsEmulation:off --app:lib '
		f'--out:{build_artifact} '
		f'{file_path}'
	).split()

	process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	out, err = [i.decode('utf-8') if i else i for i in process.communicate()]
	if err: raise Exception(err)
	
	# Make sure to hash the source file to match the build artifact
	hash_filename = file_path.name + '.hash'
	with (file_path.parent / '__pycache__' / hash_filename).open('w') as file:
		file.write(hash_file(file_path))

	return build_artifact

import hashlib
def hash_file(path):
	BLOCKSIZE = 65536
	hasher = hashlib.md5()
	with path.open('rb') as file:
		buf = file.read(BLOCKSIZE)
		while len(buf) > 0:
			hasher.update(buf)
			buf = file.read(BLOCKSIZE)
	return hasher.hexdigest()

# ext_name = 'bitmap'
# cmd = f'nim c --threads:on --tlsEmulation:off --app:lib --out:{ext_name}.pyd {ext_name}.nim'.split()

# process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
# out, err = [i.decode('utf-8') if i else i for i in process.communicate()]

# if err:
#     print('asdfadsf')
#     raise Exception(err)
# else:
#     print('->')
#     print(out)
#     print('->')

#     import bitmap
#     print(bitmap.greet('Pebaz'))

from pathlib import Path
import importlib, types

class Nimporter:
	@classmethod
	def create_module(cls, spec):
		#import ptty; ptty(globs=globals(), locs=locals())
		#return None
		#spec = importlib.util.spec_from_file_location("module.name", "/path/to/file.py")
		return importlib.util.module_from_spec(spec)

	@classmethod
	def exec_module(cls, module):
		"""
		Module executor.
		"""
		print(module)
		#import ptty; ptty(globs=globals(), locs=locals())
		return module

class Nimfinder:
	"""
	https://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
	https://blog.quiltdata.com/import-almost-anything-in-python-an-intro-to-module-loaders-and-finders-f5e7b15cda47
	"""
	def __init__(self):
		self.imported = set()
 
	@classmethod
	def find_module(cls, fullname, path=None):
		module = fullname.split('.')[-1]
		if module in self.imported:
			return None
		module_file = f'{module}.nim'

		path = path if path else []

		for search_path in [Path(i) for i in (path + sys.path + ['.']) if Path(i).is_dir()]:
			contents = [i.name for i in search_path.iterdir()]
			# TODO(pebaz): contents.extend([search down the '.'s!!])
			if module_file in contents:
				print('Found it in', search_path, module, module_file)

				module_path = search_path / module_file
				pycache = search_path / '__pycache__'
				hash_filename = module_file + '.hash'

				if pycache.exists():
					# Already compiled, check to see if the source is modified
					hash_filepath = pycache / hash_filename
					if hash_filepath.exists():
						prev_hash = hash_filepath.read_text()

						# Only compile if the source text has changed
						if prev_hash != hash_file(module_path):
							sys.path.append(str(pycache.absolute()))
							nim_compile(module_path)
				else:
					sys.path.append(str(pycache.absolute()))
					nim_compile(module_path)

				# TODO(pebaz): Compile here
				# nim_compile(module_path)

				self.imported.add(module)
				#return self
				# I solved this by compiling `bitmap` and then calling:
				# util.find_spec('bitmap')
				return importlib.machinery.ExtensionFileLoader
				
	

		print(self.__class__.__name__, 'could not find', fullname, path, f'{module}.nim')

		return None
 
	@classmethod
	def save_this_IT_WORKS_find_spec(cls, fullname, path=None, target=None):
		#import ptty; ptty(globs=globals(), locs=locals())
		#return importlib.util.spec_from_loader(fullname, importlib.machinery.ExtensionFileLoader)
		# return importlib.machinery.ModuleSpec(
		# 	name=fullname,
		# 	loader=importlib.machinery.ExtensionFileLoader,
		# 	origin=r'C:\Coding\nimpy\nimpy\__pycache__\bitmap.pyd'
		# )

		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		# This worked
		return importlib.util.spec_from_file_location('bitmap', r'C:\Coding\nimpy\nimpy\__pycache__\bitmap.pyd')


	@classmethod
	def find_spec(cls, fullname, path=None, target=None):
		module = fullname.split('.')[-1]
		module_file = f'{module}.nim'

		path = path if path else []

		ext = '.pyd' if sys.platform == 'win32' else '.so'
		build_artifact = None

		for search_path in [Path(i) for i in (path + sys.path + ['.']) if Path(i).is_dir()]:
			contents = [i.name for i in search_path.iterdir()]
			# TODO(pebaz): contents.extend([search down the '.'s!!])
			if module_file in contents:
				print('Found it in', search_path, module, module_file)

				module_path = search_path / module_file
				pycache = search_path / '__pycache__'
				hash_filename = module_file + '.hash'

				if pycache.exists():
					# Already compiled, check to see if the source is modified
					hash_filepath = pycache / hash_filename
					if hash_filepath.exists():
						prev_hash = hash_filepath.read_text()

						# Only compile if the source text has changed
						if prev_hash != hash_file(module_path):
							sys.path.append(str(pycache.absolute()))
							build_artifact = nim_compile(module_path)
							break
						else:
							build_artifact = pycache / (module + ext)
				else:
					sys.path.append(str(pycache.absolute()))
					nim_compile(module_path)
					build_artifact = pycache / (module + ext)
					break

		return importlib.util.spec_from_file_location(
			fullname,
			location=str(build_artifact.absolute())
		)
		

	def load_module(self, name):
		raise ImportError("%s is blocked and cannot be imported" % name)
		# m = types.ModuleType(name, f'This is a docstring for {name}')
		# sys.modules[name] = m

		# return m
		# TODO(pebaz): Simply do a programatic import here

		# THIS WILL LOOP FOREVER
		return importlib.import_module(name)
		#return imp.load_compiled(name)

#importlib.machinery.SOURCE_SUFFIXES.insert(0, '.nim')
sys.path_importer_cache.clear()
importlib.invalidate_caches()

#sys.meta_path.insert(0, Nimfinder())
sys.meta_path.append(Nimfinder())

print(sys.path)
import math
import esper
import tkinter.messagebox
import raylib.colors

import bitmap
print(bitmap.greet('Pebaz'))
#print(sys.modules)
