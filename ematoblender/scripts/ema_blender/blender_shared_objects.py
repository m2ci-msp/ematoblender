__author__ = 'Kristy'


# sound actuator for streaming
soundpath = None
vidpath = None
mocappath = None

# materials


# armatures
updateable_armatures_names = []

# tongue top empty name
tongue_top_empty_name = lambda i: 'TSurfEmp{}'.format(str(i).zfill(2))
tongue_top_empties = []

# cubes that get data
ema_mesh_name_rule = lambda i: 'CoilCube{}'.format(str(i).zfill(2))
ema_inferred_name_rule = lambda i: 'InferredCube{}'.format(str(i).zfill(2))

all_ema_meshes = []  # list of the cone objects that will later display data in order created

# tuple of index and meshobject and placename
ema_biteplate_meshes = []
ema_reference_meshes = []
ema_active_meshes = []
ema_inferred_meshes = []

# iterator over the lists of tuples above that re-evaluates whenever run
from ..ema_shared.miscellanous import ReeevalIter
ema_driven_meshes = ReeevalIter('bsh.ema_biteplate_meshes', 'bsh.ema_reference_meshes', 'bsh.ema_active_meshes')


# local_json_copy
local_json_copy=None

# tongue armature
tongue_pointer_bones = []  # collects the names of the bones that have IK constraints
matched_ik_coils_bones = []  # collects the names of the pointer bones and the coil they IK to as tuples

tongue_control_empties = {'TB':None, 'TM':None, 'TT':None}  # connect to objects that show the positions from emadata

# cameras # must be same as bpy.data.objects
circling_cam = 'CircularCamera'
circling_cam_empty = None


# empties that move lips
sidelip_mover = None
sidelip_follower = None


# streaming xml
streaming_xml = None


# the clientserver when running
gameserver = None
gs_soc_blocking = None  # socket object with connection to gameserver
gs_soc_nonblocking = None
gs_answers = None
head_inversion = None
latest_df = None
latest_status = None