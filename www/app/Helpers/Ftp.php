<?php
/**
 * FTP Class.
 *
 * @author David Carr - dave@daveismyname.com
 *
 * @version 1.0
 * @date June 27, 2014
 * @date updated Sept 19, 2015
 */
namespace Helpers;

/**
 * Interact with remote FTP Server.
 */
class Ftp
{
    /**
     * Hold the FTP connection.
     *
     * @var int
     */
    private $conn;

    /**
     * Holds the path relative to the root of the server.
     *
     * @var string
     */
    private $basePath;

    /**
     * Open a FTP connection.
     *
     * @param string $host the server address
     * @param string $user username
     * @param string $pass password
     * @param string $base the public folder usually public_html or httpdocs
     */
    public function __construct($host, $user, $pass, $base)
    {
        //set the basepath
        $this->basePath = $base.'/';

        //open a connection
        $this->conn = ftp_connect($host);

        //login to server
        ftp_login($this->conn, $user, $pass);
    }

    /**
     * Close the connection.
     */
    public function close()
    {
        ftp_close($this->conn);
    }

    /**
     * Create a directory on the remote FTP server.
     *
     * @param string $dirToCreate name of the directory to create
     */
    public function makeDirectory($dirToCreate)
    {
        if (!file_exists($this->basePath.$dirToCreate)) {
            ftp_mkdir($this->conn, $this->basePath.$dirToCreate);
        }
    }

    /**
     * Delete directory from FTP server.
     *
     * @param string $dir foldr to delete
     */
    public function deleteDirectory($dir)
    {
        ftp_rmdir($this->conn, $this->basePath.$dir);
    }

    /**
     * Set folder permission.
     *
     * @param string $folderChmod folder name
     * @param int    $permission  permission value
     *
     * @return string success message
     */
    public function folderPermission($folderChmod, $permission)
    {
        if (ftp_chmod($this->conn, $permission, $folderChmod) !== false) {
            return "<p>$folderChmod chmoded successfully to ".$permission."</p>\n";
        }
    }

    /**
     * Upload file to FTP server.
     *
     * @param string $remoteFile path and filename for remote file
     * @param string $localFile  local path to file
     *
     * @return string message
     */
    public function uploadFile($remoteFile, $localFile)
    {
        if (ftp_put($this->conn, $this->basePath.$remoteFile, $localFile, FTP_ASCII)) {
            return "<p>successfully uploaded $localFile to $remoteFile</p>\n";
        } else {
            return "<p>There was a problem while uploading $remoteFile</p>\n";
        }
    }

    /**
     * Delete remove file.
     *
     * @param string $file path and filename
     */
    public function deleteFile($file)
    {
        ftp_delete($this->conn, $this->basePath.$file);
    }
}
