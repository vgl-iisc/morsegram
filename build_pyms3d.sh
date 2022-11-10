git clone https://bitbucket.org/vgl_iisc/mscomplex-3d.git
cd mscomplex-3d
git submodule update --init --recursive
mkdir build install
cmake-gui
cd build
numProc=$(grep -c ^processor /proc/cpuinfo)
echo "Total number of processor : "$numProc
make -j$numProc
make -j$numProc install