rm -rf ./build ./dist
python3 setup.py sdist bdist_wheel
twine upload dist/* --password ${PYPI_PASSWORD} --username ${PYPI_USERNAME}
rm -rf ./build ./dist