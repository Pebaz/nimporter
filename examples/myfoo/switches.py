import sys

print(MODULE_PATH)

if sys.platform == 'win32':
    __switches__ = [
    'nimble',
    'c',
    '--accept',
    '--app:lib',
    '-d:release',
    '--opt:speed',
    '-d:ssl'

    __switches__ = {
        'import' : [
            'nimble',
            'c',
            '--accept',
            '--app:lib',
            '-d:release',
            '--opt:speed',
            '-d:ssl',
            f'--out:{BUILD_ARTIFACT}',
            f'{MODULE_PATH}'
        ],
        'bundle' : ['nimble', 'cc', 'c', '--accept']
    }

else:
    __switches__ = {
        'import' : [
            'nimble',
            'c',
            '--accept',
            '--app:lib',
            '-d:release',
            '--opt:speed',
            '-d:ssl',
            f'--out:{BUILD_ARTIFACT}',
            f'{MODULE_PATH}'
        ],
        'bundle' : ['nimble', 'cc', 'c', '--accept']
    }
