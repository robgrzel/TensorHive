from setuptools import setup, find_packages
from tensorhive.core.utils.colors import red, orange, green
import tensorhive


def copy_configuration_files():
    '''
    Copies `main_config.ini` and `hosts_config.ini` to `~/.config/TensorHive/`.
    Prints are only visible when `pip install ... --verbose` (it's handled by pip itself)
    '''
    import shutil
    from pathlib import PosixPath
    target_dir = PosixPath.home() / '.config/TensorHive'
    # Destination is given explicitely, just in case we'd want to rename file during the installation process
    hosts_config_path = {'src': 'hosts_config.ini', 'dst': str(target_dir / 'hosts_config.ini')}
    config_path = {'src': 'main_config.ini', 'dst': str(target_dir / 'main_config.ini')}
    
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(hosts_config_path['src'], hosts_config_path['dst'])
        shutil.copy(config_path['src'], config_path['dst'])    

        print(green('Configuration .ini files copied to {}'.format(target_dir)))
        print(orange('Please, remember to customize hosts_config.ini before launching TensorHive!'))
    except:
        print(red('Unable to copy configuration files to {}'.format(target_dir)))


setup(
    name = 'tensorhive',
    version = tensorhive.__version__,
    license='Apache License 2.0',
    packages = find_packages(),
    include_package_data=True,
    entry_points = {
        'console_scripts': [
            'tensorhive = tensorhive.__main__:main'
        ],
    },
    # TODO @roscisz Add classifiers https://pypi.org/pypi?%3Aaction=list_classifiers
    # TODO @roscisz Add `platforms` argument
    # TODO @roscisz Validate description correctness
    description = 'Lightweight computing resource management tool for executing distributed TensorFlow programs',
    author = 'Pawel Rosciszewski, Michał Martyniak, Filip Schodowski, Tomasz Menet',
    author_email = 'pawel.rosciszewski@pg.edu.pl',
    url = 'https://github.com/roscisz/TensorHive',
    download_url = 'https://github.com/roscisz/TensorHive/archive/{version}.tar.gz'.format(version=tensorhive.__version__),
    keywords = 'distributed machine learning tensorflow resource management',
    install_requires=[
        'parallel-ssh', 
        'passlib', 
        'sqlalchemy', 
        'sqlalchemy-utils', 
        'click', 
        'connexion', 
        'flask_cors', 
        'gunicorn', 
        'coloredlogs'
    ],
    zip_safe=False
)

copy_configuration_files()