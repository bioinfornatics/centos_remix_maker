from bs4        import BeautifulSoup
from remote     import get_html, download_file, find_item_from_url
from utils      import uncompress_file, find_filename, rm, command
from os         import path, makedirs, sep, chdir, getcwd
from sqlite3    import connect
from shutil     import copyfile

class Repo:


    def __get_repo_content( self ):
        baseurl = ""
        if self.__baseurl != "":
            baseurl = self.__baseurl
        elif self.__mirrorlist != "":
            baseurl = get_baseurl_from_mirror( self.__mirrorlist )

        url     = baseurl + 'Packages/'
        html    = get_html( url )
        soup    = BeautifulSoup( html, "lxml" )
        rpmfiles = map(
                        lambda y: y["href"],
                        soup.body.find_all( lambda x : x.name == 'a' and  x["href"].endswith(".rpm") and "minimal" in  x["href"]  )
                     )
        return set( rpmfiles )


    def __get_baseurl_from_mirror( self ):
        raise NotImplementedError


    def __get_value(  self, repoline, property_name ):
        pattern     = "--" + property_name + "="
        name        = ""
        start_pos   = repoline.find( pattern )
        start_pos2  = start_pos + len(pattern)
        end_pos     = -1
        if start_pos != -1:

            end_pos = repoline[ start_pos2 : ].find( ' ' )
            if end_pos!= -1:
                name = repoline[start_pos2 : end_pos + start_pos2 ]
            else:
                name = repoline[start_pos2 : ].rstrip()
        print(name)
        return name


    def __init__(self, repoline):
        #value = self.__get_value( repoline, "name"         )
        #self = self._replace(name=value)
        self.__name       = self.__get_value( repoline, "name"         )
        self.__baseurl    = self.__get_value( repoline, "baseurl"      )
        self.__mirrorlist = self.__get_value( repoline, "mirrorlist"   )
        if self.__baseurl == "":
            if self.__mirrorlist != "":
                self.__baseurl = self.__get_baseurl_from_mirror( )
            else:
                 raise Exception( "[Error] repo need to provides a baseur or a mirrorlist" )
        self.__type       = self.__baseurl[ : self.__baseurl.find(':') ]
        #self.rpmfiles   = __get_repo_content()


    @property
    def name(self):
        return self.__name


    @property
    def baseurl(self):
        return self.__baseurl


    @property
    def mirrorlist(self):
        return self.__mirrorlist


    @property
    def type(self):
        return self.__type


#####################################
class RepoData:

    def __get_primarydb( self ):
        url             = self.__repo.baseurl + "/repodata/"
        primarydb_path  = ""
        if self.__repo.type == "http":
            primarydb = find_item_from_url( url, lambda x : x.name == 'a' and "primary.sqlite" in x["href"] )
            if primarydb != None :
                primarydb_url = primarydb['href']
                compressedFile  = download_file( url + primarydb_url, self.__directory )
                primarydb_path  = path.join( self.__directory, "primary.sqlite")
                uncompress_file( compressedFile, primarydb_path )
                return  primarydb_path
            else :
                raise Exception( "No links found." )
            #primarydb_url   = find_item_from_url( url, lambda x : x.name == 'a' and x["href"].endswith( "-primary.sqlite.xz" ) or x["href"].endswith( "-primary.sqlite.bz2" ) )['href']
            #compressedFile  = download_file( url + primarydb_url, self.__directory )
            #primarydb_path  = path.join( self.__directory, "primary.sqlite")
            #uncompress_xz_file( compressedFile, primarydb_path )
            #uncompress_bz2_file( compressedFile, primarydb_path )
        


    def __get_compsXML( self ):
        url             = self.__repo.baseurl + "/repodata/"
        comps_file      = None
        if self.__repo.type == "http":
            comps_url       = find_item_from_url( url, lambda x : x.name == 'a' and x["href"].endswith( "-comps.xml" ) )
            if comps_url is not None:
                comps_file = download_file( url + comps_url['href'].rstrip(), self.__directory )
        return comps_file


    def __get_soup( self ):
        content = ""
        soup    = None
        if self.__comps is not None:
            with open(self.__comps, "r" ) as xml:
                content = xml.read()
            soup = BeautifulSoup( content, "lxml" )
        return soup


    def __init__(self, repo, repodata_dir, discinfo = ""):
        if not path.exists( repodata_dir ):
            makedirs( repodata_dir )
        self.__repo       = repo
        self.__directory  = repodata_dir
        self.__primarydb  = self.__get_primarydb()
        self.__comps      = self.__get_compsXML()
        self.__cursor     = connect(self.__primarydb).cursor()
        self.__soup       = self.__get_soup()

    @property
    def directory(self):
        return self.__directory


    @property
    def repo(self):
        return self.__repo


    @property
    def comps(self):
        return self.__comps


    def createrepo( self, treeDirs, discinfo, name ):
        if self.__comps != None and discinfo != "":
            comps   = path.join( treeDirs.iso_custom_path, "repodata", "comps.xml" )
            copyfile( self.__comps, comps )
            cache   = path.abspath( path.join(treeDirs.cache_path,"createrepo", name ) )
            old_dir = getcwd()
            comps   = comps.replace( treeDirs.iso_custom_path, "" )
            chdir( treeDirs.iso_custom_path )
            command(  "createrepo --update -dp -s sha -u media://{0} -c {1} -g {2} --repo={3} .".format( discinfo, cache, comps, name ), verbose = True )
            #command(  "createrepo --update -dvp -c {0} -g {1} .".format( cache, comps ), verbose = True )
            chdir( old_dir )

    def has_group( self, group_name ):
        result = False
        if self.__soup is not None:
            group_id    = self.__soup.find( "id", text = group_name )
            if group_id is not None:
                result = True
        return result


    def get_packages_from_group( self, group_name ):
        group_id    = self.__soup.find( "id", text = group_name )
        group       = None
        result      = []
        if group_id is not None:
            group   = group_id.find_parent( "group" )
            result  = [ item.text for item in group.find_all( "packagereq", type="default" )]
            result += [ item.text for item in group.find_all( "packagereq", type="mandatory" )]
        return set(result)


    def has_package( self, name ):
        result  = False
        if '*' in name:
            result = self.has_package_like( name )
        else:
            result = self.has_package_strict( name )
        return result


    def has_package_strict( self, name ):
        self.__cursor.execute("SELECT count(name) FROM packages WHERE name = ?", (name,) )
        result  = False
        counter = self.__cursor.fetchone()[0]
        if counter >= 1:
            result = True
        return result


    def has_package_like( self, name ):
        name    = name.replace( '*', '%' )
        self.__cursor.execute("SELECT count(name) FROM packages WHERE name LIKE ?", (name,) )
        result  = False
        counter = self.__cursor.fetchone()[0]
        if counter >= 1:
            result = True
        return result


    def get_package_url( self, name ):
        result  = None
        if '*' in name:
            result = self.get_package_url_like( name )
        else:
            result = [ self.get_package_url_strict( name ) ]
        return result


    def get_package_url_strict( self, name ):
        self.__cursor.execute("SELECT location_href FROM packages WHERE name = ?", (name,) )
        return self.__cursor.fetchone()[0]


    def get_package_url_like( self, name ):
        name    = name.replace( '*', '%' )
        self.__cursor.execute("SELECT location_href FROM packages WHERE name LIKE ?", (name,) )
        return [ element[0] for element in self.__cursor.fetchall() ]


    def get_package_version( self, name ):
        result  = False
        if '*' in name:
            result = [ self.get_package_version_strict( name ) ]
        else:
            result = self.get_package_version_like( name )
        return result


    def get_package_version_strict( self, name ):
        self.__cursor.execute("SELECT version FROM packages WHERE name = ?", (name,) )
        version = self.__cursor.fetchone()[0]
        return version



    def get_package_version_like( self, name ):
        name    = name.replace( '*', '%' )
        self.__cursor.execute("SELECT version FROM packages WHERE name LIKE ?", (name,) )
        return [ element[0] for element in self.__cursor.fetchall() ]


    def get_packages_keys(self, name ):
        keys  = []
        if '*' in name:
            keys = self.get_packages_keys_like( name )
        else:
            keys = [ self.get_package_key_strict( name ) ]
        return keys


    def get_package_key_strict(self, name ):
        key = ""
        self.__cursor.execute("SELECT pkgKey FROM packages WHERE name = ?", (name,) )
        key = self.__cursor.fetchone()[0]
        return key


    def get_packages_keys_like(self,  name):
        result = []
        name    = name.replace( '*', '%' )
        self.__cursor.execute( "SELECT pkgKey FROM  packages WHERE name LIKE ?", (name,) )
        result = [ element[0] for element in self.__cursor.fetchall() ]
        return result


    def get_packages_name(self,  pkgKeys):
        result = []
        if len(pkgKeys) > 0:
            sql = "SELECT name FROM  packages WHERE pkgKey in ("
            sql += "".join( [ str(pkgKey) + "," for pkgKey in pkgKeys ] )
            sql = sql[:-1] + ')'
            self.__cursor.execute( sql )
            result = [ element[0] for element in self.__cursor.fetchall() ]
        return result


    def get_packages_required(self,  pkgKeys):
        result = []
        if len(pkgKeys) > 0:
            sql = "SELECT name FROM  requires WHERE pkgKey in ("
            sql += "".join( [ str(pkgKey) + "," for pkgKey in pkgKeys ] )
            sql = sql[:-1] + ')'
            self.__cursor.execute( sql )
            result = [ element[0] for element in self.__cursor.fetchall() ]
        return result


    def get_packages_provided(self, requires_list ):
        result = []
        if len(requires_list) > 0:
            sql = "SELECT pkgKey FROM  provides WHERE name in ("
            sql += "".join( [ "'" + item + "'," for item in requires_list ] )
            sql
            sql = sql[:-1] + ')'
            self.__cursor.execute( sql )
            result = [ element[0] for element in self.__cursor.fetchall() ]
        return result


    def get_package_dependencies(self, name ):
        dependencies  = []
        if '*' in name:
            dependencies = self.get_packages_dependencies_like( name )
        else:
            dependencies = self.get_package_dependencies_strict( name )
        return set(dependencies)


    def get_package_dependencies_strict(self, name ):
        dependencies = []
        key             = self.get_packages_keys( name )
        requires_list   = self.get_packages_required( key )
        provides_list   = self.get_packages_provided( requires_list )
        return self.get_packages_name( provides_list )


    def get_packages_dependencies_like(self, name ):
        pkgKeys     = self.get_packages_keys( name )
        result      = [ ]
        for n in  self.get_packages_name( pkgKeys ):
            result +=  self.get_package_dependencies( n )
        return result





#####################################
def init_repodata( repo_list, treeDirs, discinfo ):
    repodata_list = set()
    for repo in repo_list:
        repo_cache = path.join( treeDirs.cache_path, "createrepo", repo.name )
        if not path.exists(repo_cache):
            makedirs(repo_cache)
        repodata = RepoData( repo, repo_cache )
        repodata.createrepo( treeDirs, discinfo, repodata.repo.name )
        repodata_list.add( repodata )
        
    return repodata_list

def cleaning_repodata( treeDirs ):
    # rm( treeDirs.iso_custom_path + sep + "*.bz2"  )
    # rm( treeDirs.iso_custom_path + sep + "*.gz"  )
    for tbl in find_filename( treeDirs.iso_custom_path, "TRANS.TBL" ):
        rm( tbl )

def find_os_repodata( repodata_list, version, arch):
    isSearching = True
    result      = ""
    iterator    = repodata_list.__iter__()
    repodata    = None
    try: repodata    = iterator.next()
    except StopIteration: isSearching= False
    while isSearching:
        is_os_repo = repodata.repo.baseurl.endswith( "/{0}/os/{1}/".format( version, arch ) )
        if is_os_repo and repodata.comps is not None:
            result = repodata.comps
        try: repodata = iterator.next()
        except StopIteration: isSearching= False
    return result
