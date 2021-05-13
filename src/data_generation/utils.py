import re
import numpy as np
from pathlib import Path


def extract_file_name(path, suffix='stl'):
    """
    Extracts the name of the file with the given suffix
    :param path:
    :param suffix:
    :return: Name of the file
    """
    file_name = path.split('/')[-1]
    file_name = re.sub('.' + suffix + '$', '', file_name)
    return file_name


def binvox2npz(path_voxel_model: str, label: np.array = None) -> np.ndarray:

    # TODO: Adjust label handover. For now it is included in order not to forget it later!

    with open(path_voxel_model, 'rb') as file:
        model = _read_as_3d_array(file)

    filepath = Path(path_voxel_model).with_suffix('.npz')
    np.savez_compressed(filepath, model=model, label=label)

    return np.array(model.data)


def _read_binvox_header(fp):
    """ Read binvox header. Internal use. """
    line = fp.readline().strip()
    if not line.startswith(b'#binvox'):
        raise IOError('Not a binvox file')
    dims = list(map(int, fp.readline().strip().split(b' ')[1:]))
    translate = list(map(float, fp.readline().strip().split(b' ')[1:]))
    scale = list(map(float, fp.readline().strip().split(b' ')[1:]))[0]
    line = fp.readline()
    return dims, translate, scale


def _read_as_3d_array(fp, fix_coords=True):
    """
    Read binary binvox format as array.
    Returns the model data.
    Voxels are stored in a three-dimensional numpy array, which is simple and
    direct, but may use a lot of memory for large models. (Storage requirements
    are 8*(d^3) bytes, where d is the dimensions of the binvox model. Numpy
    boolean arrays use a byte per element).
    """
    dims, translate, scale = _read_binvox_header(fp)
    raw_data = np.frombuffer(fp.read(), dtype=np.uint8)
    # if just using reshape() on the raw data:
    # indexing the array as array[i,j,k], the indices map into the
    # coords as:
    # i -> x
    # j -> z
    # k -> y
    # if fix_coords is true, then data is rearranged so that
    # mapping is
    # i -> x
    # j -> y
    # k -> z
    values, counts = raw_data[::2], raw_data[1::2]
    data = np.repeat(values, counts).astype(np.bool)
    data = data.reshape(dims)
    if fix_coords:
        # xzy to xyz TODO the right thing
        data = np.transpose(data, (0, 2, 1))
        axis_order = 'xyz'
    else:
        axis_order = 'xzy'
    return data
