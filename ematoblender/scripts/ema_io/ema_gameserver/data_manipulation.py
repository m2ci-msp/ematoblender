__author__ = 'Kristy'
import math

from . import biteplate_headcorr as hc
from ...ema_blender import coil_info as ci


#######################
# NOTE: TO RUN THESE FUNCTIONS YOU WILL NEED MATHUTILS INSTALLED IN YOUR LOCAL PYTHON ENVIRONMENT.
# TO DO SO: DOWNLOAD blender_mathutils‑2.74‑cp34‑none‑win32.whl FROM http://www.lfd.uci.edu/~gohlke/pythonlibs/#blender-mathutils
# IN THE DOWNLOAD DIRECTORY TYPE pip install [filename]
#######################

def matrix_to_list(matrix):
    return [list(x) for x in matrix]


def remove_outliers(df_list):
    """From a list/queue of data frames, set any values to nan for any coil/dimension the values are in the lower/upper quartile."""
    all_coils = [df.give_coils() for df in df_list]
    print('first coils look like:', df_list[0].give_coils())
    # for each different place
    for i in range(len(all_coils[0])):
        x, y, z = [], [], []
        # for each dataframe, get the data
        for df in all_coils:
            xi, yi, zi = df[i].abs_loc
            x.append(xi)
            y.append(yi)
            z.append(zi)
        # x,y,z are now lists of all the values over all dfs
        x.sort()
        y.sort()
        z.sort()
        x_lower, x_upper = x[math.floor(len(x)/4)], x[-math.floor(len(x)/4)]
        y_lower, y_upper = y[math.floor(len(y)/4)], y[-math.floor(len(y)/4)]
        z_lower, z_upper = z[math.floor(len(z)/4)], z[-math.floor(len(z)/4)]

        # for each dataframe reset some data
        for df in all_coils:
            xi, yi, zi = df[i].abs_loc
            if xi < x_lower or xi > x_upper:
                x = 'nan'
            if yi < y_lower or yi > y_upper:
                y = 'nan'
            if zi < z_lower or zi > z_upper:
                z = 'nan'
            #TODO: check how nans are handled
    return df_list


def remove_first_ms_of_list(df_list, ms=100):
    print('THIS IS MY DATAFRAME LIST', df_list)
    microsecs = ms * 1000
    first_ts = df_list[0].components[0].timestamp
    limit = microsecs + first_ts
    print('limit is', limit)
    return [df for df in df_list if df.components[0].timestamp >= limit]


def head_corr_bp_correct(df, biteplate_refspace, headpos_refspace):

    if biteplate_refspace is None or headpos_refspace is None:
        # no biteplate recording available, return the raw data only
        print('No biteplate_refspace, no correction', biteplate_refspace, headpos_refspace)
        return df

    else:
        print('biteplate_refspace is', biteplate_refspace)

    print('df being corrected:', df, 'coils', df.give_coils())

    # isolate the coil objects
    active, biteplate, reference = ci.get_sensor_roles_no_blender()
    refcoils = [df.give_coils()[reference[x][0]] for x in range(len(reference))]
    print('refcoils', refcoils)
    print('active', active)
    current_rs = ReferencePlane(*[x.abs_loc for x in refcoils[:3]]) # todo: this could be a source of error - are these the correct coils?


    if not biteplate_refspace.ui_origin:  # ON FIRST ACTIVE SENSOR READING
        print('\n\n\n This is the first reading of the active sensors.')
        # set the origin of the biteplate CS as UI
        ui_index = [x[0] for x in active if x[2] == 'UI'][0]
        ui_coil = df.give_coils()[ui_index]
        ui_coil.ref_loc = current_rs.project_to_lcs(ui_coil.abs_loc)
        biteplate_refspace.set_origin(ui_coil.ref_loc)

    # FOR EACH SAMPLE
    for c in df.give_coils():
        # transform locations relative to reference sensors (get head-corrected locations in global space)
        #print('current coil being corrected', c)
        c.ref_loc = tuple(current_rs.project_to_lcs(c.abs_loc))
        # transform ALL locations from head-corrected space to biteplane space.
        c.bp_corr_loc = tuple(biteplate_refspace.project_to_lcs(c.ref_loc))
        #print('one coil\'s new location', c.bp_corr_loc)

    inverted_cam_position = biteplate_refspace.project_to_lcs(
                                #headpos_refspace.project_to_lcs(
                                    current_rs.project_to_lcs(headpos_refspace.origin)
                                #)
    )
    inverted_cam_position = [x for x in inverted_cam_position]
    print('inverted cam', inverted_cam_position)

    print('returning df with change', df.give_coils()[0].abs_loc,df.give_coils()[0].bp_corr_loc)
    print(current_rs.give_local_to_global_mat(listed=True))
    return df, \
            matrix_to_list(current_rs.give_global_to_local_mat()*biteplate_refspace.give_global_to_local_mat()), \
            inverted_cam_position
