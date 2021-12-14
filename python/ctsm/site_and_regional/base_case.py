"""
This module includes the definition for a parent class for SinglePointCase
and RegionalCase. The common functionalities of SinglePointCase and
RegionalCase are defined in this Class.
"""
# -- Import libraries

# -- standard libraries
import os
import logging
import subprocess

from datetime import date
from getpass import getuser

# -- 3rd party libraries
import numpy as np
import xarray as xr

# -- import local classes for this script
from ctsm.git_utils import get_git_short_hash

logger = logging.getLogger(__name__)


class BaseCase:
    """
    Parent class to SinglePointCase and RegionalCase

    ...

    Attributes
    ----------
    create_domain : bool
        flag for creating domain file
    create_surfdata : bool
        flag for creating surface dataset
    create_landuse : bool
        flag for creating landuse file
    create_datm : bool
        flag for creating DATM files

    Methods
    -------
    create_1d_coord(filename, lon_varname , lat_varname,x_dim , y_dim )
        create 1d coordinate variables to enable sel() method

    add_tag_to_filename(filename, tag)
       add a tag and timetag to a filename ending with
       [._]cYYMMDD.nc or [._]YYMMDD.nc

    update_metadata(nc)
        Class method for adding some new attributes (such as date, username) and
        remove the old attributes from the netcdf file.
    """

    def __init__(self, create_domain, create_surfdata, create_landuse, create_datm):
        """
        Initializes BaseCase with the given arguments.

        Parameters
        ----------
        create_domain : bool
            Flag for creating domain file a region/single point
        create_surfdata : bool
            Flag for creating domain file a region/single point
        create_landuse : bool
            Flag for creating landuse file a region/single point
        create_datmdata : bool
            Flag for creating datm files a region/single point
        """
        self.create_domain = create_domain
        self.create_surfdata = create_surfdata
        self.create_landuse = create_landuse
        self.create_datm = create_datm

    def __str__(self):
        """
        Converts ingredients of the BaseCase to string for printing.
        """
        return (
            str(self.__class__)
            + "\n"
            + "\n".join(
                (
                    str(item) + " = " + str(self.__dict__[item])
                    for item in sorted(self.__dict__)
                )
            )
        )

    @staticmethod
    def create_1d_coord(filename, lon_varname, lat_varname, x_dim, y_dim):
        """
        Create 1d coordinate variables for a netcdf file to enable sel() method

        Parameters
        ----------
            filename (str) : name of the netcdf file
            lon_varname (str) : variable name that has 2d lon
            lat_varname (str) : variable name that has 2d lat
            x_dim (str) : dimension name in X -- lon
            y_dim (str): dimension name in Y -- lat

        Raises
        ------
            None

        Returns
        -------
            f_out (xarray Dataset): Xarray Dataset with 1-d coords

        """
        logging.debug("Open file: " + filename)
        f_in = xr.open_dataset(filename)

        # create 1d coordinate variables to enable sel() method
        lon0 = np.asarray(f_in[lon_varname][0, :])
        lat0 = np.asarray(f_in[lat_varname][:, 0])
        lon = xr.DataArray(lon0, name="lon", dims=x_dim, coords={x_dim: lon0})
        lat = xr.DataArray(lat0, name="lat", dims=y_dim, coords={y_dim: lat0})

        f_out = f_in.assign({"lon": lon, "lat": lat})

        f_out.reset_coords([lon_varname, lat_varname])
        f_in.close()
        return f_out

    @staticmethod
    def add_tag_to_filename(filename, tag):
        """
        Add a tag and replace timetag of a filename
        Expects file to end with [._]cYYMMDD.nc or [._]YYMMDD.nc
        Add the tag to just before that ending part
        and change the ending part to the current time tag.

        Parameters
        ----------
            filename (str) : file name
            tag (str) : string of a tag to be added to the end of filename

        Raises
        ------
            Error: When it cannot find . and _ in the filename.

        Returns
        ------
            fname_out (str): filename with the tag and date string added

        """
        basename = os.path.basename(filename)
        cend = -10
        if basename[cend] == "c":
            cend = cend - 1
        if (basename[cend] != ".") and (basename[cend] != "_"):
            logging.error(
                "Trouble figuring out where to add tag to filename:" + filename
            )
            os.abort()
        today = date.today()
        today_string = today.strftime("%y%m%d")
        fname_out = basename[:cend] + "_" + tag + "_c" + today_string + ".nc"
        return fname_out

    def update_metadata(self, nc):
        """
        Class method for adding some new attributes (such as date, username) and
        remove the old attributes from the netcdf file.

        Parameters
        ----------
            nc (xarray dataset) :
                Xarray dataset of netcdf file that we'd want to update it's metadata.

        Raises
        ------
            None

        Returns
        ------
            None

        """
        # update attributes
        today = date.today()
        today_string = today.strftime("%Y-%m-%d")

        # get git hash
        sha = get_git_short_hash()

        nc.attrs["Created_on"] = today_string
        nc.attrs["Created_by"] = getuser()
        nc.attrs["Created_with"] = os.path.abspath(__file__) + " -- " + sha

        # delete unrelated attributes if they exist
        del_attrs = [
            "source_code",
            "SVN_url",
            "hostname",
            "history" "History_Log",
            "Logname",
            "Host",
            "Version",
            "Compiler_Optimized",
        ]
        attr_list = nc.attrs

        for attr in del_attrs:
            if attr in attr_list:
                logging.debug("This attr should be deleted : " + attr)
                del nc.attrs[attr]

        # for attr, value in attr_list.items():
        #    print (attr + " = "+str(value))
