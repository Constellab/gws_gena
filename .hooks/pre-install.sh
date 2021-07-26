# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


# Pre-installation script executed before server installation

# ensure gaia is ready!
python3 "/lab/.core/bricks/gaia/.hooks/pre-install.py"
bash "/lab/.core/bricks/gaia/.hooks/pre-install.sh"

point="fba"
gena_dir="/lab/.core/externs/gena-cpp"
if [ ! -d "${gena_dir}" ]; then
    mkdir -p $gena_dir
fi

out_dir="/lab/.core/bricks/gena/bin/fba"
if [ ! -d "${out_dir}" ]; then
    mkdir -p $out_dir
fi

# skip if already compiled
if [ ! -f "${out_dir}/${point}" ]; then
    cd $gena_dir
    bazel build gena:${point}

    cp "${gena_dir}/bazel-bin/gena/${point}" "${out_dir}/${point}"
    chmod a+x ${out_dir}/${point}
fi