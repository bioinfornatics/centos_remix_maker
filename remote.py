import urllib.request as urllib2
from os         import path
from bs4        import BeautifulSoup
from utils      import progress

#####################################
def get_html( url ):
    response    = urllib2.urlopen( url )
    html        = response.read()
    return html


#####################################
def get_centos_mirror_list( version, arch ):
    mirror_page = 'http://isoredirect.centos.org/centos/{0}/isos/{1}/'.format(version, arch)
    url         =find_item_from_url( mirror_page, lambda x : x.name == 'a' and "isos" in x["href"]   )
    if url != None:
      return url['href'].rstrip()
    else:
      raise Exception("No mirrors found")


#####################################
def get_minimal_iso_url( url ):
    filename    = find_item_from_url( url, lambda x : x.name == 'a' and  x["href"].endswith(".iso") and "Minimal" in  x["href"]  )["href"]
    return url + '/' + filename


#####################################
def find_item_from_url( url, predicate ):
    print(url)
    html        = get_html( url )
    soup        = BeautifulSoup( html, "lxml" )
    return  soup.body.find( predicate )


#####################################
def download_file( url, outputdir, force = False, verbose = False ):
    file_name           = path.join( outputdir, url.split('/')[-1] )
    allow_downloading   = False
    status              = ""

    if not path.exists( file_name ) or force == True:
        allow_downloading = True

    if allow_downloading:
        outfile     = open( file_name, 'wb')
        response    = urllib2.urlopen( url )
        meta        = response.info()
        file_size   = int(meta.get("Content-Length")[0])
        msg         = "Downloading: %s Bytes: %s" % (file_name, file_size)
        file_size_dl    = 0
        block_sz        = 8192
        while True:
            buffer = response.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            outfile.write(buffer)
            if verbose:
                status = progress(file_size_dl, file_size, msg)
                print(status),
        outfile.close()
        if verbose:
            print("")
    return file_name


#####################################
def download_iso( version, arch, outDir ):
    mirror_page = get_centos_mirror_list( version, arch )
    iso_url     = get_minimal_iso_url( mirror_page )
    isoFile     = download_file( iso_url, outDir, verbose = True )
    return isoFile

