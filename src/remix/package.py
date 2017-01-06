from glob       import glob
from os         import chdir, path
from sys        import stderr
from utils      import command, progress
from repo       import Repo
from remote     import download_file



#####################################
def extract_repo_list( kickstart_path ):
    isReading           = True
    repo                = set()

    with open( kickstart_path, "r" ) as kickstart:
        while isReading:
            line = kickstart.readline()
            if line.startswith("%packages"):
                isReading = False
            elif line.startswith("repo"):
                repo.add( Repo( line ) )
            else:
                continue
    return repo

#####################################
def get_availlable_package( repo_list ):
    repos = {}
    for repo in repo_list:
        repos[ repo.name ] = get_repo_content( repo )
    return repos


#####################################
def find_package( name, repodata_list ):
    isSearching = True
    repo        = None
    pattern     = name + "-"
    iterator    = repodata_list.__iter__()
    repodata    = None
    try: repodata    = iterator.__next__()
    except StopIteration: isSearching= False
    while isSearching:
        if repodata.repo.type == "http" and repodata.has_package( name ):
            isSearching = False
            repo        = repodata
        else:
            try: repodata = iterator.__next__()
            except StopIteration: isSearching= False
    if repo is None:
        stderr.write( "Package {0} not Found\n".format( name ) )
    return repo


#####################################
def find_group( group_name, repodata_list ):
    isSearching = True
    repo        = None
    pattern     = group_name + "-"
    iterator    = repodata_list.__iter__()
    repodata    = None
    try: repodata    = iterator.__next__()
    except StopIteration: isSearching= False
    while isSearching:
        if repodata.has_group( group_name ):
            isSearching = False
            repo        = repodata
        else:
            try: repodata = iterator.__next__()
            except StopIteration: isSearching= False
    if repo is None:
        stderr.write( "Group {0} not Found\n".format( group_name ) )
    return repo


#####################################
def extract_package_list( kickstart_path, repodata_list ):
    print("Extacting packages choosen from kickstart")
    inPackageSection    = False
    isReading           = True
    packages            = set()

    with open( kickstart_path, "r" ) as kickstart:
        #cmd = "repoquery --qf=%{name} -g --list --grouppkgs=all "
        while isReading:
            line = kickstart.readline()
            if not inPackageSection and line.startswith("%packages"):
                inPackageSection = True
            elif inPackageSection:
                if line.startswith("%end"):
                    inPackageSection = False
                    isReading        = False
                elif line.startswith("@"):
                    #stdout = command( cmd + line[1:] )
                    #[ packages.add( p ) for p in stdout.split( '\n' ) ]
                    repodata  = find_group( line[1:].strip(), repodata_list )
                    if repodata is not None:
                        packages  |= repodata.get_packages_from_group( repodata_list )
                elif not line.startswith("#"):
                    if not line.startswith("-"):
                        packages.add( line.strip() )
    return packages


#####################################
def get_existing_package( workdir ):
    msg = "Listing rpm files"
    cmd = "rpm -qp --queryformat '%{NAME}'"
    packages            = set()
    index               = 0
    rpm_list            = glob( workdir + "/*.rpm" )
    stdout              = None

    for rpm in rpm_list:
        stdout = command( cmd + rpm, pass_exception = True )
        packages.add( stdout )
        print(progress( index,  len(rpm_list), msg )),
        index += 1
    print(progress( index,  len(rpm_list), msg ))

    return packages


#####################################
def get_missing_package( packagesNeed, packagesOrigin, repodata_list, verbose = False ):
    msg                     = "Resolving dependencies"
    packagesToDownload      = packagesNeed.difference( packagesOrigin )
    index                   = 0
    packagesNotFound        = set()

    for package in packagesToDownload:
        repodata        = find_package( package, repodata_list )
        if repodata is not None:
            packagesNeed   |= repodata.get_package_dependencies( package )
        else:
            packagesNotFound.add( package )
        if verbose: print(progress( index,  len(packagesToDownload),msg )),
        index += 1
    max_value = len(packagesToDownload)
    if max_value == 0:
        if index != 0:
            max_value = index
        else:
            max_value   = 1
            index       = 1
    if verbose: print(progress( index,  max_value, msg ))

    packagesToDownload = packagesNeed.difference( packagesOrigin )
    packagesToDownload = packagesToDownload.difference( packagesNotFound )

    return packagesToDownload


#####################################
def download_packages(workdir, packagesToDownload, repodata_list ):
    msg                 = "Downloading rpm files to resolve dependencies"
    packages_dir        = path.join( workdir, "Packages" )
    index               = 0
    repodata            = None
    packagesNotFound    = set()
    for package in packagesToDownload:
        if package is not None and package != "":
            repodata    = find_package( package, repodata_list )
            if repodata is not None:
                for url in repodata.get_package_url( package ):
                    u = repodata.repo.baseurl + url
                    download_file( u, packages_dir )
        print(progress( index,  len(packagesToDownload), msg )),
        index += 1
    print(progress( index,  len(packagesToDownload), msg ))
