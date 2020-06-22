from setuptools import setup


with open('README.md') as readme:
    long_description = readme.read()


setup(
    name='pynbs',
    version='0.4.0',
    license='MIT',
    description='A simple python library to read and write .nbs files from Note Block Studio',
    long_description=long_description,
    long_description_content_type='text/markdown',

    author='Valentin Berlier',
    author_email='berlier.v@gmail.com',
    url='https://github.com/vberlier/pynbs',

    platforms=['any'],
    python_requires='>=2.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='note-block-studio minecraft nbs-files',

    py_modules=['pynbs'],
)
