from subprocess import Popen, PIPE
from sys        import stderr
from bz2        import BZ2File
from os         import getcwd, path, remove, walk, close
from glob       import glob
from datetime   import date
from tempfile   import mkstemp
from shutil     import move
import shlex
import lzma


def command( line, verbose = False, pass_exception = False ):
    if verbose:
        print("Executing: ", line)
    p = Popen( shlex.split( line ) , stdout = PIPE, stderr = PIPE )
    out, err = p.communicate()
    if len(err) != 0 and not pass_exception:
        for e in err.splitlines():
            stderr.write( "[Warning] " + e.strip().decode('utf-8') + '\n' )
        raise Exception( "command failled: " + line  )
    return out

def uncompress_bz2_file( compressedFile, outputFile ):
    bzFile          = BZ2File( compressedFile, "rb", 20 * 4096)
    with open( outputFile, "wb" ) as out:
        out.write( bzFile.read() )

def uncompress_xz_file( compressedFile, outputFile ):
    xzFile          = lzma.open( compressedFile, "rb")
    with open( outputFile, "wb" ) as out:
        out.write( xzFile.read() )

def uncompress_file( compressedFile, outputFile ):
    print(compressedFile)
    if compressedFile.endswith("bz2"):
        uncompress_bz2_file( compressedFile, outputFile )
    elif compressedFile.endswith("xz"):
        uncompress_xz_file( compressedFile, outputFile )
    else:
        raise Exception( "Unsupported format"+compressedFile )

def mount_iso( isoFile, mountPoint ):
    command("mount -t iso9660 -o loop,ro {0} {1}".format( isoFile , mountPoint ), verbose = True )



def umount( mountPoint ):
    command("umount {0}".format( mountPoint ), verbose = True )


def rm( glob_file ):
    for f in glob( glob_file ):
        remove( f )


def progress( current_value, max_value, msg ):
    if max_value == 0:
        max_value = 0.01
    percentage  = current_value * 100. / max_value
    message     = r"%s  [%3.2f%%]" % ( msg, percentage )
    status      = message + chr(8)*(len(message)+1)
    return status


def find_files( root, predicate ):
    return map( predicate, walk(root) )


def find_filename( root, filename ):
    return filter( lambda y:y != None, find_files( root, lambda x: path.join(x[0], filename) if filename in x[2] else None  ) )


def find_file_endswith( root, ends_part ):
    filenames = set() 
    for data_file in find_files( root, None ):
        for filename in data_file[2]:
            if filename.endswith( ends_part ):
                filenames.add( filename )
    return filenames
        


def make_iso( iso_name, root ):
    today = date.today()
    cmd = "mkisofs -r -N -L -d -R -J -T  -quiet -no-emul-boot -boot-load-size 4 -boot-info-table -V '{iso_name}' -A '{iso_name} - {iso_date}' -b isolinux/isolinux.bin  -c isolinux/boot.cat -x 'lost+found' -joliet-long  -o '{iso_name}.iso' '{root}'".format( iso_name=iso_name, iso_date=today.isoformat(),  root=root )
    command( cmd, verbose = True)


def sed( file_path, pattern, subst, max_time=0 ):
    #Create temp file
    fh, abs_path = mkstemp()
    with open(abs_path,'w') as new_file:
        with open(file_path ,'r') as old_file:
            changed     = 0
            for line in old_file:
                if line.find( pattern ) >= 0 and line.find( subst ) == -1:
                    if (max_time != 0 and changed < max_time) or max_time == 0:
                        changed += 1
                        new_file.write(line.replace(pattern, subst))
                    else:
                        new_file.write(line)
                else:
                    new_file.write(line)
    #close temp file
    close(fh)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)
