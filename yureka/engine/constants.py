import os


# Time control
TC_WTIME = 'wtime'
TC_BTIME = 'btime'
TC_WINC = 'winc'
TC_BINC = 'binc'
TC_MOVESTOGO = 'movestogo'
TC_MOVETIME = 'movetime'
TC_KEYS = [
    TC_WTIME,
    TC_BTIME,
    TC_WINC,
    TC_BINC,
    TC_MOVESTOGO,
    TC_MOVETIME,
]

root_path = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

# UCI Policy Engine
DEFAULT_MODEL = 'Policy.v2'
DEFAULT_MODEL_FILE = os.path.join(
    root_path,
    'saved_models',
    'Policy.v2',
    'Policy.v2_2018-06-14_12:03:03_33.model',
)

# UCI MCTS Engine
RANDOM_POLICY = 'random'
DEFAULT_VALUE = 'Value.v2'
DEFAULT_VALUE_FILE = os.path.join(
    root_path,
    'saved_models',
    'Value.v2',
    'Value.v2_2018-06-12_15:11:36_6.model',
)
ZERO_VALUE = 'zero'
DEFAULT_POLICY = 'Policy.v2'
DEFAULT_POLICY_FILE = os.path.join(
    root_path,
    'saved_models',
    'Policy.v2',
    'Policy.v2_2018-06-14_12:03:03_33.model',
)
DEFAULT_RESNET = 'ResNet.v0'
DEFAULT_RESNET_TOWER_FILE = os.path.join(
    root_path,
    'saved_models',
    'ResNet.v0',
    'Tower_2018-06-14_22:32:44_12.model',
)
DEFAULT_RESNET_VALUE_FILE = os.path.join(
    root_path,
    'saved_models',
    'ResNet.v0',
    'ValueHead_2018-06-14_22:32:45_12.model',
)
DEFAULT_RESNET_POLICY_FILE = os.path.join(
    root_path,
    'saved_models',
    'ResNet.v0',
    'PolicyHead_2018-06-14_22:32:44_12.model',
)
