# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


# Pre-installation script executed before server installation

dlib_build_dir="/lab/.gws/externs/dlib-cpp/build"
ready_file="$dlib_build_dir/READY"

n=1
while [ ! -f "$ready_file" ]; do
    echo "$n - Dlib build is not ready. Sleep 10 secs ..."
    sleep 10
    n=$(( $n + 1 ))
done

point="fba"
gena_dir="/lab/gws/externs/gena-cpp"

if [ ! -d "${gena_dir}" ]; then
    mkdir -p $gena_dir
fi

cd $gena_dir
bazel build gena:${point}

out_dir="/lab/gws/bricks/gena/bin/fba"
if [ ! -d "${out_dir}" ]; then
    mkdir -p $out_dir
fi

cp "${gena_dir}/bazel-bin/gena/${point}" "${out_dir}/${point}"
chmod a+x ${out_dir}/${point}