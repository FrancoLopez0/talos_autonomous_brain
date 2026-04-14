from setuptools import find_packages, setup
import os

package_name = 'autonomous_rover_brain'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config/prompts'), ['config/prompts/system.md']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='lopez',
    maintainer_email='francoalelopez@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            # 'nombre_del_ejecutable = nombre_del_paquete.nombre_del_archivo:main'
            'langchain_node = autonomous_rover_brain.langchain_node:main'
        ],
    },
)
