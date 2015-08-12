# -*- coding: utf-8 -*-
"""
Created on Mon Jul 31 15:53:14 2015

@author: uwe
"""

import pandas as pd


class Power_Plants:
    """
    Main-Interface for loading weather data.

    """

    def __init__(self):
        self.plants = None

    def get_all_power_plants(self, conn, geometry):
        self.plants = self.get_all_ee_power_plants(conn, geometry)
        self.plants = pd.concat([self.plants, self.get_all_fossil_power_plants(
            conn, geometry)], ignore_index=True)
        return self.plants

    def get_all_ee_power_plants(self, conn, geometry,):
        sql = """
            SELECT anlagentyp, anuntertyp, p_nenn_kwp
            FROM deutschland.eeg_03_2013 as ee
            WHERE st_contains(ST_GeomFromText('{wkt}',4326), ee.geom)
            """.format(wkt=geometry.wkt)
        return pd.DataFrame(
            conn.execute(sql).fetchall(), columns=[
                'type', 'subtype', 'p_kw_peak'])

    def get_all_fossil_power_plants(self, conn, geometry):
        sql = """
            SELECT auswertung, ersatzbrennstoff, el_nennleistung
            FROM vn.geo_power_plant_bnetza_2014 as pp
            WHERE st_contains(
            ST_GeomFromText('{wkt}',4326), ST_Transform(pp.geom, 4326))
            """.format(wkt=geometry.wkt)
        return pd.DataFrame(
            conn.execute(sql).fetchall(), columns=[
                'type', 'subtype', 'p_kw_peak'])