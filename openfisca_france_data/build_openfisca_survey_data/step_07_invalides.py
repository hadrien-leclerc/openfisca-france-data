#! /usr/bin/env python
# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
from numpy import where

from openfisca_france_data.build_openfisca_survey_data import load_temp, save_temp
from openfisca_france_data.build_openfisca_survey_data.utils import control, print_id

log = logging.getLogger(__name__)


def invalide(year = 2006):

    log.info(u"Entering 07_invalides: construction de la variable invalide")
# # # Invalides
# # #inv = caseP (vous), caseF (conj) ou case G, caseI, ou caseR (pac)

# # loadTmp("final.Rdata")
# # invalides <- final[,c("noindiv","idmen","caseP","caseF","idfoy","quifoy")]
# # invalides <- within(invalides,{
# #   caseP <- ifelse(is.na(caseP),0,caseP)
# #   caseF <- ifelse(is.na(caseF),0,caseF)
# #   inv <- FALSE})
# # # Les "vous" invalides
# # table(invalides[,c("caseF","quifoy")],useNA="ifany")
# # invalides[(invalides$caseP==1) & (invalides$quifoy=="vous"),"inv"] <- TRUE
# #

    log.info(u"Etape 1 : création de la df invalides")
    log.info(u"    1.1 : déclarants invalides")
    final = load_temp(name = "final", year = year)
    invalides_vars = [
        "caseF",
        "caseP",
        "idfoy",
        "idmen",
        "noindiv",
        "quifoy",
        ]

    aah_eec_variables = ["rc1rev", "maahe"]
    aah_eec = False

    if set(aah_eec_variables) < set(final.columns):
        aah_eec = True
        invalides_vars += aah_eec

    assert set(invalides_vars) < set(final.columns), \
        "Variables {} are missing".format(set(invalides_vars).difference(set(final.columns)))

    invalides = final.xs(invalides_vars, axis = 1)

    for var in ["caseP", "caseF"]:
        assert invalides[var].notnull().all(), 'NaN values in {}'.format(var)

    # Les déclarants invalides
    invalides['inv'] = False
    invalides['inv'][(invalides['caseP'] == 1) & (invalides['quifoy'] == 0)] = True
    log.info(u"Il y a {} invalides déclarants".format(invalides["inv"].sum()))

    # Les personnes qui touchent l'aah dans l'enquête emploi
    if aah_eec:
        log.info(u"Inspecting rc1rev")
        log.info(invalides['rc1rev'].value_counts())


        invalides['inv'][invalides.maahe > 0] = True
        invalides['inv'][invalides.rc1rev == 4] = True  # TODO: vérifier le format.
        log.info(u"Il y a {} invalides qui touchent des alloc").format(invalides["inv"].sum())

    print_id(invalides)

# # # Les conjoints invalides
# #
# # #men_inv_conj <- invalides[c("idmen","caseF","quifoy")]
# # #men_inv_conj <- rename(men_inv_conj, c("caseF"="inv"))
# # #table(men_inv_conj[men_inv_conj$inv==1 ,c("inv","quifoy")],useNA="ifany")
# # # Il y a des caseF suir des conjoints cela vint des doubles d?clarations TODO: shoumd clean this
# # #toto <- invalides[invalides$caseF==1 & invalides$quifoy=="conj","idmen"]
# # #load(indm)
# # #titi <- indivim[(indivim$ident %in% toto) & (indivim$persfip=="vous" |indivim$persfip=="conj") ,c("ident","noindiv","declar1","declar2","persfip","quelfic")]
# # #titi <- titi[order(titi$ident),]
# # foy_inv_conj <- invalides[,c("idfoy","caseF","quifoy")]
# # foy_inv_conj <- rename(foy_inv_conj, c("caseF"="inv"))
# # table(foy_inv_conj[ ,c("inv","quifoy")],useNA="ifany")
# # # On ne garde donc que les caseF des "vous"

# # foy_inv_conj   <- foy_inv_conj[foy_inv_conj$quifoy=="vous",c("idfoy","inv")]
# # table(foy_inv_conj[ ,c("inv")],useNA="ifany")
# # invalides_conj <- invalides[invalides$quifoy=="conj",c("idfoy","noindiv")]
# # invalides_conj <- merge(invalides_conj, foy_inv_conj, by="idfoy", all.x=TRUE)
# # table(invalides_conj$inv) # TODO en 2006 On en a 316 au lieu de 328 il doit y avoir de idfoy avec caseF qui n'ont pas de vous because double déclaration'
# # invalides[invalides$quifoy=="conj",c("idfoy","noindiv","inv")] <- invalides_conj
# # table(invalides[,c("inv","quifoy")],useNA="ifany")
# # rm(invalides_conj,foy_inv_conj)

    # On récupère les idfoy des foyers avec une caseF cochée
    log.info('    1.2 : Les conjoints invalides')
    idfoy_inv_conj = final.idfoy[final.caseF].copy()
    inv_conj_condition = (invalides.idfoy.isin(idfoy_inv_conj) & (invalides.quifoy == 1))
    invalides["inv"][inv_conj_condition] = True

    log.info(u"Il y a {} invalides conjoints".format(len(invalides[inv_conj_condition])))
    log.info(u" Il y a {} invalides déclarants et invalides conjoints".format(invalides["inv"].sum()))

# # # Enfants invalides et garde alternée
# #
# # loadTmp("pacIndiv.Rdata")
# # foy_inv_pac <- invalides[!(invalides$quifoy %in% c("vous","conj")),c("inv","noindiv")]
# # foy_inv_pac <- merge(foy_inv_pac, pacIndiv[,c("noindiv","typ","naia")], by="noindiv",all.x =TRUE)
# # names(foy_inv_pac)
# # table(foy_inv_pac[,c("typ","naia")],useNA="ifany")
# # table(foy_inv_pac[,c("typ")],useNA="ifany")
# # foy_inv_pac <- within(foy_inv_pac,{
# #   inv  <- (typ=="G") | (typ=="R") | (typ=="I") | (typ=="F" & (as.numeric(year)-naia>18))
# #   alt  <- (typ=="H") | (typ=="I")
# #   naia <- NULL
# #   typ  <- NULL})
# #
# # table(foy_inv_pac[ ,c("inv")],useNA="ifany")
# # table(foy_inv_pac[ ,c("alt")],useNA="ifany")
# # invalides$alt <- 0
# # foy_inv_pac[is.na(foy_inv_pac$alt),"alt"] <- 0
# # invalides[!(invalides$quifoy %in% c("vous","conj")),c("noindiv","inv","alt")] <- foy_inv_pac
    log.info(u"    1.3 : enfants invalides et garde alternée")
    pacIndiv = load_temp(name='pacIndiv', year=year)
    print pacIndiv.type_pac.value_counts()

    foy_inv_pac = invalides[['noindiv', 'inv']][~(invalides.quifoy.isin([0, 1]))].copy()
#     pac = pacIndiv.ix[:, ["noindiv", "type_pac", "naia"]]
    print len(foy_inv_pac)

    print pacIndiv.columns
    foy_inv_pac = foy_inv_pac.merge(
        pacIndiv[['noindiv', 'type_pac', 'naia']].copy(),
        on = 'noindiv',
        how = 'left',
        )
    foy_inv_pac['inv'] = (
        foy_inv_pac['type_pac'].isin(['G', 'R', 'I']) |
        (
            (foy_inv_pac.type_pac == "F") & ((year - foy_inv_pac.naia) > 18)
            )
        )

    foy_inv_pac['alt'] = ((foy_inv_pac.type_pac == "H") | (foy_inv_pac.type_pac == "I"))
    foy_inv_pac['naia'] = None
    foy_inv_pac['type_pac'] = None
    foy_inv_pac['alt'] = foy_inv_pac['alt'].fillna(False)

    print foy_inv_pac['inv'].describe()
    invalides['alt'] = 0
    foy_inv_pac['alt'][foy_inv_pac.alt.isnull()] = 0
    invalides = invalides.merge(foy_inv_pac, on=["noindiv", "inv", "alt"])

    invalides = invalides.drop_duplicates(['noindiv', 'inv', 'alt'], take_last = True)
#     print foy_inv_pac.inv.value_counts() # TODO: JS : trop peu de True là-dedans
#     print foy_inv_pac.alt.value_counts() #
#
#
#     print  len(invalides), len(foy_inv_pac)
#     print invalides.inv.value_counts()

    invalides = invalides.merge(foy_inv_pac, on = 'noindiv', how = 'left')
    invalides['inv'] = where(invalides['inv_y'], invalides['inv_y'], invalides['inv_x'])
    invalides['alt'] = where(invalides['inv_y'], invalides['inv_y'], invalides['inv_x'])

    invalides = invalides.loc[:, ["noindiv", "idmen", "caseP", "caseF", "idfoy", "quifoy", "inv", 'alt']]
    invalides['alt'].fillna(False, inplace = True)

    print invalides.inv.value_counts()
    invalides = invalides.drop_duplicates(['noindiv', 'inv', 'alt'], take_last = True)
    del foy_inv_pac, pacIndiv

# # # Initialisation des NA sur alt et inv
# # invalides[is.na(invalides$inv), "inv"] <- 0
# # table(invalides[,c("alt","inv")],useNA="ifany")
# #
# # final <- merge(final, invalides[,c("noindiv","inv","alt")], by="noindiv",all.x=TRUE)
# # table(final[, c("inv","alt")],useNA="ifany")

    print ''
    print 'Etape 2 : Initialisation des NA sur alt et inv'
    assert invalides["inv"].notnull().all() & invalides.alt.notnull().all()
    final = final.merge(invalides[['noindiv', 'inv', 'alt']].copy(), on = 'noindiv', how = 'left')
    del invalides

    print final.inv.value_counts()
    control(final, debug = True)

    save_temp(final, name = 'final', year = year)
    print 'final complétée et sauvegardée'

if __name__ == '__main__':
    year = 2006
    invalide(year = year)
