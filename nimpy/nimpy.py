"""
1. Nim Compiler Invoker
2. Nim Import Hook
3. Nim Build Artifact Cacher
	Compile and then store in __pycache__
"""

import sys, subprocess, importlib, hashlib
from pathlib import Path

class NimCompilerException(Exception):
	def __init__(self, msg):
		nim_module, error_msg = msg.split(' Error: ')
		self.nim_module = nim_module
		self.error_msg = error_msg
	
	def __str__(self):
		# TODO(pebaz): Print out the lines of code that messed up
		# with open(self.nim_module, 'r') as nim:
		# 	print()

		return self.error_msg + 'at ' + self.nim_module

class NimCompiler:
	EXT = '.pyd' if sys.platform == 'win32' else '.so'

	@classmethod
	def pycache_dir(cls, module_path):
		return module_path.parent / '__pycache__'

	@classmethod
	def hash_filename(cls, module_path):
		return cls.pycache_dir(module_path) / (module_path.name + '.hash')

	@classmethod
	def is_cache(cls, module_path):
		return NimCompiler.pycache_dir(module_path).exists()

	@classmethod
	def is_hashed(cls, module_path):
		"""
		Looks in `path.parent / '__pycache__'` for `path.name + '.hash'`.
		"""
		return cls.hash_filename(module_path).exists()

	@classmethod
	def is_built(cls, module_path):
		return NimCompiler.build_artifact(module_path).exists()

	@classmethod
	def get_hash(cls, module_path):
		return cls.hash_filename(module_path).read_bytes()

	@classmethod
	def hash_changed(cls, module_path):
		if not NimCompiler.is_hashed(module_path):
			return True
		return cls.get_hash(module_path) != NimCompiler.hash_file(module_path)

	@classmethod
	def hash_file(cls, module_path):
		block_size = 65536
		hasher = hashlib.md5()
		with module_path.open('rb') as file:
			buf = file.read(block_size)
			while len(buf) > 0:
				hasher.update(buf)
				buf = file.read(block_size)
		return hasher.digest()

	@classmethod
	def update_hash(cls, module_path):
		with cls.hash_filename(module_path).open('wb') as file:
			file.write(cls.hash_file(module_path))

	@classmethod
	def build_artifact(cls, module_path):
		return cls.pycache_dir(module_path) / (module_path.stem + cls.EXT)

	@classmethod
	def compile(cls, module_path, release_mode=False):
		build_artifact = cls.build_artifact(module_path)

		nimc_cmd = (
			f'nim c --threads:on --tlsEmulation:off --app:lib '
			f'--hints:off --parallelBuild:0 '
			f'{"-d:release" if release_mode else ""}'
			f'--out:{build_artifact} '
			f'{module_path}'
		)

		#process = subprocess.Popen(nimc_cmd.split(), shell=True, stdout=subprocess.PIPE)
		#out, err = [i.decode('utf-8') if i else '' for i in process.communicate()]

		process = subprocess.run(nimc_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = process.stdout, process.stderr
		out = out.decode() if out else ''
		err = err.decode() if err else ''

		# Handle any compiler errors
		NIM_COMPILE_ERROR = ' Error: '
		if NIM_COMPILE_ERROR in err:
			raise NimCompilerException(err)
		elif NIM_COMPILE_ERROR in out:
			raise NimCompilerException(out)
		
		cls.update_hash(module_path)

		return build_artifact


class Nimporter:  # TODO(pebaz): Allow for failed compilation
	@classmethod
	def find_spec(cls, fullname, path=None, target=None):
		# TODO(pebaz): Add support for dot importing
		module = fullname.split('.')[-1]
		module_file = f'{module}.nim'
		path = list(path) if path else []  # Ensure that path is always a list

		search_paths = [
			Path(i)
			for i in (path + sys.path + ['.'])
			if Path(i).is_dir()
		]

		for search_path in search_paths:
			contents = set(i.name for i in search_path.iterdir())

			# NOTE(pebaz): Found an importable/compileable module
			if module_file in contents:
				module_path = search_path / module_file

				should_compile = any([
					NimCompiler.hash_changed(module_path),
					not NimCompiler.is_cache(module_path),
					not NimCompiler.is_built(module_path)
				])

				if should_compile:
					build_artifact = NimCompiler.compile(module_path)
				else:
					build_artifact = NimCompiler.build_artifact(module_path)
				
				return importlib.util.spec_from_file_location(
					fullname,
					location=str(build_artifact.absolute())
				)


sys.path_importer_cache.clear()
importlib.invalidate_caches()

'''
By putting the Nimpoter at the end of the list of module loaders, it ensures
that Nim code files are imported only if there is not a Python module of the
same name somewhere on the path.
'''
sys.meta_path.append(Nimporter())

print(sys.path)
import math
import esper
import tkinter.messagebox
import raylib.colors

import bitmap
print(bitmap.greet('Pebaz'))
print(dir(bitmap))

from foo.bar import baz
print(baz('Purple Boo'))
