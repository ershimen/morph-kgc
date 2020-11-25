import argparse, os, re, logging, sys
import multiprocessing as mp
from configparser import ConfigParser, ExtendedInterpolation


def dir_path(dir_path):
    """
    Checks that a directory exists. If the directory does not exist, create the directories in the path.

    :param dir_path: the path to the directory
    :type dir_path: str
    :return valid path to the directory
    :rtype str
    """

    dir_path = str(dir_path)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    return dir_path


def file_path(file_path):
    """
    Checks that directories in a file path exist. If they do not exist, create the directories.

    :param file_path: the path to the log file
    :type file_path: str
    :return the path to the log file
    :rtype str
    """

    file_path = str(file_path).strip()
    if not os.path.exists(os.path.dirname(file_path)):
        if os.path.dirname(file_path):
            os.makedirs(os.path.dirname(file_path))

    return file_path


def file_name(file_name):
    """
    Generates a valid file name.

    :param file_name: the original file name
    :type file_name: str
    :return the valid file name
    :rtype str
    """

    file_name = str(file_name).strip()
    file_name.replace(' ', '_')
    file_name = re.sub(r'(?u)[^-\w.]', '', file_name)

    return file_name


def existing_file_path(file_path):
    """
    Checks if a file exists.

    :param file_path: the file path
    :type file_path: str
    :return the file path
    :rtype str
    """

    file_path = str(file_path).strip()
    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError("%r is not a valid file path." % file_path)

    return file_path


def process_number(number):
    """
    Generates a natural number from a given number. Number is converted to int.
    In case of been 0, the number of cores in the system is generated.

    :param number: number
    :type number: str
    :return natural number
    :rtype int
    """

    whole_number = int(number)
    if whole_number < 0:
        raise ValueError
    elif whole_number == 0:
        whole_number = mp.cpu_count()

    return whole_number


def natural_number_including_zero(number):
    """
    Generates a natural number (including zero) from a given number.

    :param number: number
    :type number: str
    :return natural number (including zero)
    :rtype int
    """

    whole_number = int(number)
    if whole_number < 0:
        raise ValueError

    return whole_number


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generate a knowledge graph from heterogeneous data sources.',
        epilog='Transform your data into knowledge.',
        allow_abbrev=False,
        argument_default=argparse.SUPPRESS
    )

    parser.add_argument('-c', '--config', type=existing_file_path, required=True,
                        help='path to the configuration file')
    parser.add_argument('-o', '--output_dir', default='output', type=str,
                        help='path to the directory storing the results')
    parser.add_argument('-f', '--all_in_one_file', type=str,
                        help='if a file name is specified, all the results will be stored in this file. '
                             'If no file is specified the results will be stored in multiple files.')
    parser.add_argument('-r', '--remove_duplicates', default='yes', type=str,
                        choices=['yes', 'no', 'on', 'off', 'true', 'false', '0', '1'],
                        help='whether to remove duplicate triples in the results')
    parser.add_argument('-g', '--group_mappings', nargs='?', default='', const='sp',
                        choices=['s', 'p', 'sp'],
                        help='grouping criteria for mappings. The following criteria and its combinations are '
                             'possible: s: subject, p: predicate, g: named graph')
    parser.add_argument('-n', '--number_of_processes', default=1, type=process_number,
                        help='number of parallel processes. 0 to set it to the number of CPUs in the system.')
    parser.add_argument('-s', '--chunksize', default=0, type=natural_number_including_zero,
                        help='maximum number of rows of data processed at once by a process')
    parser.add_argument('-l', '--logs', nargs='?', const='', type=str,
                        help='file path to write logs to')
    parser.add_argument('-v', '--version', action='version', version='Morph-RDFizer 0.1')

    return parser.parse_args()


def validate_config(config):

    '''Validate options corresponding to the CONFIGURATION section of the configuration file'''

    if config.has_option('CONFIGURATION', 'output_dir'):
        config.set('CONFIGURATION', 'output_dir', dir_path(config.get('CONFIGURATION', 'output_dir')))

    if config.has_option('CONFIGURATION', 'all_in_one_file'):
        config.set('CONFIGURATION', 'output_dir', file_name(config.get('CONFIGURATION', 'all_in_one_file')))

    if config.has_option('CONFIGURATION', 'remove_duplicates'):
        remove_duplicates = config.get('CONFIGURATION', 'remove_duplicates')
        remove_duplicates = str(remove_duplicates).lower().strip()
        valid_options = ['yes', 'no', 'on', 'off', 'true', 'false', '0', '1']
        if remove_duplicates not in valid_options:
            error_msg = 'Option remove_duplicates of CONFIGURATION section in the configuration file ' \
                        'must be in: ' + str(valid_options)
            logging.error(error_msg)
            raise ValueError(error_msg)

    if config.has_option('CONFIGURATION', 'group_mappings'):
        group_mappings = config.get('CONFIGURATION', 'group_mappings')
        group_mappings = str(group_mappings).lower().strip()
        valid_options = ['', 's', 'p', 'sp']
        if group_mappings not in valid_options:
            error_msg = 'Option group_mappings of CONFIGURATION section in the configuration file ' \
                        'must be in: ' + str(valid_options)
            raise ValueError(error_msg)

    if config.has_option('CONFIGURATION', 'number_of_processes'):
        config.set('CONFIGURATION', 'number_of_processes',
                   str(process_number(config.get('CONFIGURATION', 'number_of_processes'))))

    if config.has_option('CONFIGURATION', 'chunksize'):
        config.set('CONFIGURATION', 'chunksize',
                   str(natural_number_including_zero(config.get('CONFIGURATION', 'chunksize'))))

    if config.has_option('CONFIGURATION', 'logs'):
        config.set('CONFIGURATION', 'logs', file_path(config.get('CONFIGURATION', 'logs')))

    '''Validate options corresponding to the SOURCES sections of the configuration file'''

    '''
        TODO:
            - Validate mappings file paths
            - validate mapping are correct
            - validate (or infer) mapping language
            - validate mapping groups criteria (according to mapping group assumption)
            - validate mappings have no errors
            - check there are no missing options for the sources
    '''

    return config


def complete_config_file_with_args(config, args):
    """
    Completes missing options in the configuration file with the options provided via arguments.
    Options specified in the configuration file are prioritized, i.e., if the option is specified in
    the configuration file the option in the arguments is ignored.

    :param config: the ConfigParser object
    :param args: the argparse object
    :return: ConfigParser object extended with information from arguments
    """

    '''create section CONFIGURATION if nor indicated in the config file'''
    if not config.has_section('CONFIGURATION'):
        config.add_section('CONFIGURATION')

    '''if parameters are not provided in the config file, take them from arguments'''
    '''mind that ConfigParser store options as strings'''
    if not config.has_option('CONFIGURATION', 'output_dir'):
        config.set('CONFIGURATION', 'output_dir', args.output_dir)
    if not config.has_option('CONFIGURATION', 'all_in_one_file') and 'all_in_one_file' in args:
        config.set('CONFIGURATION', 'all_in_one_file', args.all_in_one_file)
    if not config.has_option('CONFIGURATION', 'remove_duplicates'):
        config.set('CONFIGURATION', 'remove_duplicates', str(args.remove_duplicates))
    if not config.has_option('CONFIGURATION', 'group_mappings'):
        config.set('CONFIGURATION', 'group_mappings', args.group_mappings)
    if not config.has_option('CONFIGURATION', 'number_of_processes'):
        config.set('CONFIGURATION', 'number_of_processes', str(args.number_of_processes))
    if not config.has_option('CONFIGURATION', 'chunksize'):
        config.set('CONFIGURATION', 'chunksize', str(args.chunksize))
    if not config.has_option('CONFIGURATION', 'logs') and 'logs' in args:
        config.set('CONFIGURATION', 'logs', args.logs)

    return config


def parse_config():
    args = parse_arguments()

    config = ConfigParser(interpolation=ExtendedInterpolation())
    config.read(args.config)
    config = complete_config_file_with_args(config, args)
    config = validate_config(config)

    return config