"""Expand ``data/thai_gov_domains.csv`` with the broader catalogue of Thai
government and education domains.

Sources used (in priority order):

  1. The existing curated CSV — preserved as-is so this script is idempotent.
  2. ``CURATED_DOMAINS`` below — a manually-maintained snapshot of major
     Thai government bodies, state enterprises, universities and Thai
     newsroom .or.th domains compiled from publicly-available directories.
  3. Optional best-effort fetch of:
       * the English-language Wikipedia tables for Thai universities and
         ministries (these tables expose domain links in the third column).

Output: the CSV is rewritten in-place with rows sorted by category then
domain. Schema is unchanged: ``domain,agency_name,category``.

Running with ``--no-fetch`` skips network calls (Wikipedia only) so the
script remains fully offline-capable.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from typing import Iterable

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "data", "thai_gov_domains.csv")

# Categories used downstream by build_whitelist.py / dashboard reporting.
CAT_GOV = "go.th"
CAT_EDU = "ac.th"
CAT_NGO = "or.th"
CAT_BIZ = "co.th"


# ---------------------------------------------------------------------------
# Curated seed list. Each tuple = (domain, agency_name, category).
#
# Coverage targets:
#   * Cabinet, parliament, judiciary, independent constitutional bodies
#   * All 20 ministries and their major departments / sub-departments
#   * State enterprises (.co.th and .go.th forms)
#   * Universities -- public Rajamangala / Rajabhat / autonomous; private major
#   * 77 provincial websites
#   * Health-system bodies, public-broadcasting, civic foundations
#
# These are well-known public domains. The script is safe to re-run; entries
# already present in the CSV are preserved with their existing metadata.
# ---------------------------------------------------------------------------
CURATED_DOMAINS: list[tuple[str, str, str]] = [
    # --- Apex / cabinet / parliament ---
    ("thaigov.go.th", "Royal Thai Government", CAT_GOV),
    ("soc.go.th", "Secretariat of the Cabinet", CAT_GOV),
    ("opm.go.th", "Office of the Prime Minister", CAT_GOV),
    ("ops.go.th", "Office of the Permanent Secretary, PMO", CAT_GOV),
    ("parliament.go.th", "Parliament of Thailand", CAT_GOV),
    ("senate.go.th", "Senate of Thailand", CAT_GOV),
    ("dpr.go.th", "Department of Provincial Administration", CAT_GOV),
    ("ratchakitcha.soc.go.th", "Royal Thai Government Gazette", CAT_GOV),

    # --- Judiciary & independent constitutional bodies ---
    ("coj.go.th", "Courts of Justice", CAT_GOV),
    ("supremecourt.or.th", "Supreme Court of Thailand", CAT_NGO),
    ("constitutionalcourt.or.th", "Constitutional Court", CAT_NGO),
    ("admincourt.go.th", "Administrative Court", CAT_GOV),
    ("ago.go.th", "Office of the Attorney General", CAT_GOV),
    ("nacc.go.th", "Office of the NACC", CAT_GOV),
    ("oag.go.th", "Office of the Auditor General", CAT_GOV),
    ("ect.go.th", "Election Commission of Thailand", CAT_GOV),
    ("nhrc.or.th", "National Human Rights Commission", CAT_NGO),
    ("ombudsman.go.th", "Office of the Ombudsman", CAT_GOV),

    # --- Ministry of Foreign Affairs + missions ---
    ("mfa.go.th", "Ministry of Foreign Affairs", CAT_GOV),
    ("consular.mfa.go.th", "Department of Consular Affairs", CAT_GOV),
    ("vfsglobal.com", "VFS Visa (informational)", CAT_BIZ),
    ("thaiembassy.org", "Thai Embassy portal", CAT_NGO),

    # --- Ministry of Finance ---
    ("mof.go.th", "Ministry of Finance", CAT_GOV),
    ("rd.go.th", "Revenue Department", CAT_GOV),
    ("customs.go.th", "Customs Department", CAT_GOV),
    ("excise.go.th", "Excise Department", CAT_GOV),
    ("cgd.go.th", "Comptroller General's Department", CAT_GOV),
    ("pdmo.go.th", "Public Debt Management Office", CAT_GOV),
    ("fpo.go.th", "Fiscal Policy Office", CAT_GOV),
    ("treasury.go.th", "Treasury Department", CAT_GOV),
    ("sepo.go.th", "State Enterprise Policy Office", CAT_GOV),
    ("nta.go.th", "National Tobacco Authority", CAT_GOV),

    # --- Ministry of Commerce ---
    ("moc.go.th", "Ministry of Commerce", CAT_GOV),
    ("dbd.go.th", "Department of Business Development", CAT_GOV),
    ("dft.go.th", "Department of Foreign Trade", CAT_GOV),
    ("ditp.go.th", "Department of International Trade Promotion", CAT_GOV),
    ("dit.go.th", "Department of Internal Trade", CAT_GOV),
    ("ipthailand.go.th", "Department of Intellectual Property", CAT_GOV),
    ("tpso.go.th", "Trade Policy and Strategy Office", CAT_GOV),

    # --- Ministry of Education ---
    ("moe.go.th", "Ministry of Education", CAT_GOV),
    ("obec.go.th", "Office of the Basic Education Commission", CAT_GOV),
    ("ovec.go.th", "Office of the Vocational Education Commission", CAT_GOV),
    ("vec.go.th", "Vocational Education Commission", CAT_GOV),
    ("onec.go.th", "Office of the Education Council", CAT_GOV),
    ("opec.go.th", "Office of Private Education Commission", CAT_GOV),
    ("dla.go.th", "Department of Local Administration", CAT_GOV),
    ("nfe.go.th", "Office of Non-formal Education", CAT_GOV),
    ("ksp.or.th", "Teachers Council of Thailand", CAT_NGO),

    # --- Ministry of Higher Education, Science, Research and Innovation ---
    ("mhesi.go.th", "Ministry of Higher Education", CAT_GOV),
    ("mua.go.th", "Office of the Higher Education Commission", CAT_GOV),
    ("ohec.go.th", "Office of the Higher Education Commission (legacy)", CAT_GOV),
    ("most.go.th", "Ministry of Science and Technology (legacy)", CAT_GOV),
    ("ops.mhesi.go.th", "OPS, MHESI", CAT_GOV),
    ("nstda.or.th", "NSTDA", CAT_NGO),
    ("nrct.go.th", "National Research Council of Thailand", CAT_GOV),
    ("tistr.or.th", "TISTR", CAT_NGO),
    ("nimt.or.th", "National Institute of Metrology", CAT_NGO),
    ("gistda.or.th", "GISTDA", CAT_NGO),
    ("nectec.or.th", "NECTEC", CAT_NGO),

    # --- Ministry of Interior ---
    ("moi.go.th", "Ministry of Interior", CAT_GOV),
    ("dopa.go.th", "Department of Provincial Administration", CAT_GOV),
    ("disaster.go.th", "Department of Disaster Prevention", CAT_GOV),
    ("ddpm.go.th", "DDPM", CAT_GOV),
    ("dpt.go.th", "Department of Public Works", CAT_GOV),
    ("cdd.go.th", "Community Development Department", CAT_GOV),
    ("dol.go.th", "Department of Lands", CAT_GOV),
    ("bora.dopa.go.th", "Bureau of Registration Administration", CAT_GOV),

    # --- Ministry of Public Health ---
    ("moph.go.th", "Ministry of Public Health", CAT_GOV),
    ("dms.go.th", "Department of Medical Services", CAT_GOV),
    ("ddc.go.th", "Department of Disease Control", CAT_GOV),
    ("anamai.moph.go.th", "Department of Health", CAT_GOV),
    ("dmh.go.th", "Department of Mental Health", CAT_GOV),
    ("nhso.go.th", "National Health Security Office", CAT_GOV),
    ("hss.moph.go.th", "Health Service Support", CAT_GOV),
    ("fda.moph.go.th", "Food and Drug Administration", CAT_GOV),
    ("tcels.or.th", "Thailand Center of Excellence for Life Sciences", CAT_NGO),

    # --- Ministry of Labour ---
    ("mol.go.th", "Ministry of Labour", CAT_GOV),
    ("doe.go.th", "Department of Employment", CAT_GOV),
    ("labour.go.th", "Department of Labour Protection", CAT_GOV),
    ("dsd.go.th", "Department of Skill Development", CAT_GOV),
    ("sso.go.th", "Social Security Office", CAT_GOV),

    # --- Ministry of Transport ---
    ("mot.go.th", "Ministry of Transport", CAT_GOV),
    ("doh.go.th", "Department of Highways", CAT_GOV),
    ("drr.go.th", "Department of Rural Roads", CAT_GOV),
    ("dlt.go.th", "Department of Land Transport", CAT_GOV),
    ("caat.or.th", "Civil Aviation Authority of Thailand", CAT_NGO),
    ("md.go.th", "Marine Department", CAT_GOV),
    ("dot.go.th", "Department of Tourism", CAT_GOV),
    ("airportthai.co.th", "Airports of Thailand", CAT_BIZ),
    ("railway.co.th", "State Railway of Thailand", CAT_BIZ),
    ("bts.co.th", "BTS Group", CAT_BIZ),
    ("mrta.co.th", "MRTA", CAT_BIZ),

    # --- Ministry of Agriculture and Cooperatives ---
    ("moac.go.th", "Ministry of Agriculture and Cooperatives", CAT_GOV),
    ("doa.go.th", "Department of Agriculture", CAT_GOV),
    ("doae.go.th", "Department of Agricultural Extension", CAT_GOV),
    ("ldd.go.th", "Land Development Department", CAT_GOV),
    ("rid.go.th", "Royal Irrigation Department", CAT_GOV),
    ("dld.go.th", "Department of Livestock Development", CAT_GOV),
    ("fisheries.go.th", "Department of Fisheries", CAT_GOV),
    ("acfs.go.th", "ACFS", CAT_GOV),
    ("cpd.go.th", "Cooperative Promotion Department", CAT_GOV),
    ("rfd.go.th", "Royal Forest Department", CAT_GOV),

    # --- Ministry of Natural Resources and Environment ---
    ("mnre.go.th", "Ministry of Natural Resources and Environment", CAT_GOV),
    ("dnp.go.th", "Department of National Parks", CAT_GOV),
    ("dmcr.go.th", "Department of Marine and Coastal Resources", CAT_GOV),
    ("dgr.go.th", "Department of Groundwater Resources", CAT_GOV),
    ("dwr.go.th", "Department of Water Resources", CAT_GOV),
    ("pcd.go.th", "Pollution Control Department", CAT_GOV),
    ("tmd.go.th", "Thai Meteorological Department", CAT_GOV),
    ("oae.go.th", "Office of Agricultural Economics", CAT_GOV),

    # --- Ministry of Tourism and Sports ---
    ("mots.go.th", "Ministry of Tourism and Sports", CAT_GOV),
    ("dpe.go.th", "Department of Physical Education", CAT_GOV),
    ("sat.or.th", "Sports Authority of Thailand", CAT_NGO),
    ("tat.or.th", "Tourism Authority of Thailand", CAT_NGO),
    ("tourismthailand.org", "Tourism Authority (en)", CAT_NGO),

    # --- Ministry of Defence ---
    ("mod.go.th", "Ministry of Defence", CAT_GOV),
    ("rta.mi.th", "Royal Thai Army", CAT_GOV),
    ("navy.mi.th", "Royal Thai Navy", CAT_GOV),
    ("rtaf.mi.th", "Royal Thai Air Force", CAT_GOV),
    ("nso.mi.th", "Naval Special Operations", CAT_GOV),

    # --- Royal Thai Police ---
    ("royalthaipolice.go.th", "Royal Thai Police", CAT_GOV),
    ("immigration.go.th", "Immigration Bureau", CAT_GOV),
    ("highwaypolice.go.th", "Highway Police", CAT_GOV),
    ("tcsd.go.th", "Technology Crime Suppression Division", CAT_GOV),
    ("cyberpolice.go.th", "Cyber Crime Investigation Bureau", CAT_GOV),

    # --- Ministry of Social Development and Human Security ---
    ("m-society.go.th", "Ministry of Social Development", CAT_GOV),
    ("dwf.go.th", "Department of Women's Affairs", CAT_GOV),
    ("dop.go.th", "Department of Older Persons", CAT_GOV),
    ("dcy.go.th", "Department of Children and Youth", CAT_GOV),
    ("dep.go.th", "Department of Empowerment of Persons with Disabilities", CAT_GOV),

    # --- Ministry of Digital Economy and Society ---
    ("mdes.go.th", "Ministry of Digital Economy and Society", CAT_GOV),
    ("dga.or.th", "Digital Government Development Agency", CAT_NGO),
    ("etda.or.th", "Electronic Transactions Development Agency", CAT_NGO),
    ("thaicert.or.th", "ThaiCERT", CAT_NGO),
    ("ncsa.or.th", "National Cyber Security Agency", CAT_NGO),
    ("depa.or.th", "Digital Economy Promotion Agency", CAT_NGO),
    ("nbtc.go.th", "NBTC", CAT_GOV),
    ("nstda.or.th", "NSTDA", CAT_NGO),
    ("psdg.go.th", "Public Sector Development Group", CAT_GOV),

    # --- Ministry of Industry ---
    ("industry.go.th", "Ministry of Industry", CAT_GOV),
    ("diw.go.th", "Department of Industrial Works", CAT_GOV),
    ("dip.go.th", "Department of Industrial Promotion", CAT_GOV),
    ("dpim.go.th", "Department of Primary Industries and Mines", CAT_GOV),
    ("tisi.go.th", "Thai Industrial Standards Institute", CAT_GOV),
    ("ieat.go.th", "Industrial Estate Authority", CAT_GOV),

    # --- Ministry of Energy ---
    ("energy.go.th", "Ministry of Energy", CAT_GOV),
    ("dede.go.th", "Department of Alternative Energy", CAT_GOV),
    ("doeb.go.th", "Department of Energy Business", CAT_GOV),
    ("eppo.go.th", "Energy Policy and Planning Office", CAT_GOV),

    # --- Ministry of Culture ---
    ("m-culture.go.th", "Ministry of Culture", CAT_GOV),
    ("finearts.go.th", "Fine Arts Department", CAT_GOV),
    ("dra.go.th", "Department of Religious Affairs", CAT_GOV),

    # --- Bank / financial regulators (mostly .or.th) ---
    ("bot.or.th", "Bank of Thailand", CAT_NGO),
    ("set.or.th", "Stock Exchange of Thailand", CAT_NGO),
    ("sec.or.th", "Securities and Exchange Commission", CAT_NGO),
    ("oic.or.th", "Office of Insurance Commission", CAT_NGO),
    ("amlo.go.th", "Anti-Money Laundering Office", CAT_GOV),
    ("doi.go.th", "Department of Insurance (legacy)", CAT_GOV),
    ("dpa.or.th", "Deposit Protection Agency", CAT_NGO),

    # --- State enterprises and SOE banks ---
    ("ktb.co.th", "Krung Thai Bank", CAT_BIZ),
    ("gsb.or.th", "Government Savings Bank", CAT_NGO),
    ("baac.or.th", "BAAC", CAT_NGO),
    ("ghbank.co.th", "Government Housing Bank", CAT_BIZ),
    ("ibank.co.th", "Islamic Bank of Thailand", CAT_BIZ),
    ("smebank.co.th", "SME Bank", CAT_BIZ),
    ("exim.go.th", "EXIM Bank", CAT_GOV),
    ("egat.co.th", "EGAT", CAT_BIZ),
    ("pea.co.th", "Provincial Electricity Authority", CAT_BIZ),
    ("mea.or.th", "Metropolitan Electricity Authority", CAT_NGO),
    ("mwa.co.th", "Metropolitan Waterworks Authority", CAT_BIZ),
    ("pwa.co.th", "Provincial Waterworks Authority", CAT_BIZ),
    ("thailandpost.co.th", "Thailand Post", CAT_BIZ),
    ("nt.co.th", "National Telecom", CAT_BIZ),
    ("catv.co.th", "CAT Telecom (legacy)", CAT_BIZ),
    ("tot.co.th", "TOT (legacy)", CAT_BIZ),
    ("thaibevsi.co.th", "Thai Beverage SI", CAT_BIZ),
    ("krungthai-axa.co.th", "Krungthai AXA", CAT_BIZ),

    # --- Major public hospitals (.go.th / .or.th) ---
    ("siphhospital.com", "Siriraj Piyamaharajkarun Hospital", CAT_BIZ),
    ("si.mahidol.ac.th", "Siriraj Hospital", CAT_EDU),
    ("chulalongkornhospital.go.th", "King Chulalongkorn Memorial Hospital", CAT_GOV),
    ("ramathibodi.mahidol.ac.th", "Ramathibodi Hospital", CAT_EDU),
    ("pmk.ac.th", "Phramongkutklao College of Medicine", CAT_EDU),
    ("vajira.ac.th", "Vajira Hospital", CAT_EDU),
    ("nida.ac.th", "NIDA", CAT_EDU),
    ("queensavang.org", "Queen Savang Memorial Hospital", CAT_NGO),
    ("redcross.or.th", "Thai Red Cross Society", CAT_NGO),

    # --- Public broadcasting / news ---
    ("thaipbs.or.th", "Thai PBS", CAT_NGO),
    ("nbtworld.prd.go.th", "NBT World", CAT_GOV),
    ("prd.go.th", "Public Relations Department", CAT_GOV),
    ("mcot.net", "MCOT Public", CAT_NGO),
    ("nationaltv.prd.go.th", "National TV", CAT_GOV),

    # --- Public universities (autonomous + government) ---
    ("chula.ac.th", "Chulalongkorn University", CAT_EDU),
    ("mahidol.ac.th", "Mahidol University", CAT_EDU),
    ("ku.ac.th", "Kasetsart University", CAT_EDU),
    ("tu.ac.th", "Thammasat University", CAT_EDU),
    ("kmutt.ac.th", "King Mongkut's University of Technology Thonburi", CAT_EDU),
    ("kmitl.ac.th", "King Mongkut's Institute of Technology Ladkrabang", CAT_EDU),
    ("kmutnb.ac.th", "King Mongkut's University of Technology North Bangkok", CAT_EDU),
    ("cmu.ac.th", "Chiang Mai University", CAT_EDU),
    ("kku.ac.th", "Khon Kaen University", CAT_EDU),
    ("psu.ac.th", "Prince of Songkla University", CAT_EDU),
    ("buu.ac.th", "Burapha University", CAT_EDU),
    ("nu.ac.th", "Naresuan University", CAT_EDU),
    ("mfu.ac.th", "Mae Fah Luang University", CAT_EDU),
    ("mju.ac.th", "Maejo University", CAT_EDU),
    ("swu.ac.th", "Srinakharinwirot University", CAT_EDU),
    ("rmutk.ac.th", "RMUT Krungthep", CAT_EDU),
    ("rmutt.ac.th", "RMUT Thanyaburi", CAT_EDU),
    ("rmutl.ac.th", "RMUT Lanna", CAT_EDU),
    ("rmutsv.ac.th", "RMUT Srivijaya", CAT_EDU),
    ("rmutto.ac.th", "RMUT Tawan-ok", CAT_EDU),
    ("rmuti.ac.th", "RMUT Isan", CAT_EDU),
    ("rmutr.ac.th", "RMUT Rattanakosin", CAT_EDU),
    ("rmutp.ac.th", "RMUT Phra Nakhon", CAT_EDU),
    ("ssru.ac.th", "Suan Sunandha Rajabhat University", CAT_EDU),
    ("ssrru.ac.th", "Suan Sunandha Rajabhat (alt)", CAT_EDU),
    ("bsru.ac.th", "Bansomdejchaopraya Rajabhat", CAT_EDU),
    ("chandra.ac.th", "Chandrakasem Rajabhat University", CAT_EDU),
    ("dru.ac.th", "Dhonburi Rajabhat University", CAT_EDU),
    ("pcru.ac.th", "Phetchabun Rajabhat University", CAT_EDU),
    ("npru.ac.th", "Nakhon Pathom Rajabhat", CAT_EDU),
    ("nsru.ac.th", "Nakhon Sawan Rajabhat", CAT_EDU),
    ("nakhonratchasimaboardingschool.ac.th", "NR Boarding School", CAT_EDU),
    ("uru.ac.th", "Uttaradit Rajabhat", CAT_EDU),
    ("pnru.ac.th", "Phranakhon Rajabhat", CAT_EDU),
    ("vru.ac.th", "Valaya Alongkorn Rajabhat", CAT_EDU),
    ("snru.ac.th", "Sakon Nakhon Rajabhat", CAT_EDU),
    ("yru.ac.th", "Yala Rajabhat", CAT_EDU),
    ("psru.ac.th", "Pibulsongkram Rajabhat", CAT_EDU),
    ("lpru.ac.th", "Lampang Rajabhat", CAT_EDU),
    ("crru.ac.th", "Chiang Rai Rajabhat", CAT_EDU),
    ("cmru.ac.th", "Chiang Mai Rajabhat", CAT_EDU),
    ("rsu.ac.th", "Rangsit University", CAT_EDU),
    ("au.edu", "Assumption University", CAT_EDU),
    ("bu.ac.th", "Bangkok University", CAT_EDU),
    ("dpu.ac.th", "Dhurakij Pundit University", CAT_EDU),
    ("siam.edu", "Siam University", CAT_EDU),
    ("utcc.ac.th", "University of the Thai Chamber of Commerce", CAT_EDU),
    ("sripatum.ac.th", "Sripatum University", CAT_EDU),
    ("kbu.ac.th", "Kasem Bundit University", CAT_EDU),
    ("payap.ac.th", "Payap University", CAT_EDU),
    ("stou.ac.th", "Sukhothai Thammathirat Open University", CAT_EDU),
    ("ru.ac.th", "Ramkhamhaeng University", CAT_EDU),
    ("npu.ac.th", "Nakhon Phanom University", CAT_EDU),
    ("nrru.ac.th", "Nakhon Ratchasima Rajabhat", CAT_EDU),
    ("skru.ac.th", "Songkhla Rajabhat", CAT_EDU),
    ("hcu.ac.th", "Huachiew Chalermprakiet University", CAT_EDU),
    ("rbru.ac.th", "Rambhai Barni Rajabhat", CAT_EDU),
    ("cru.ac.th", "Chaiyaphum Rajabhat", CAT_EDU),
    ("sru.ac.th", "Surat Thani Rajabhat", CAT_EDU),
    ("loei.rajabhat.ac.th", "Loei Rajabhat", CAT_EDU),
    ("mcu.ac.th", "Mahachulalongkornrajavidyalaya University", CAT_EDU),
    ("mbu.ac.th", "Mahamakut Buddhist University", CAT_EDU),
    ("rta.ac.th", "Chulachomklao Royal Military Academy", CAT_EDU),
    ("npu.edu", "Naval Academy of Thailand", CAT_EDU),
    ("rtaf-academy.ac.th", "Royal Thai Air Force Academy", CAT_EDU),

    # --- Civic foundations and NGOs (.or.th) ---
    ("kanchanapisek.or.th", "Kanchanapisek Network", CAT_NGO),
    ("mfu.or.th", "Mae Fah Luang Foundation", CAT_NGO),
    ("redcross.or.th", "Thai Red Cross Society", CAT_NGO),
    ("ssir.or.th", "Stanford Social Innovation Review (TH)", CAT_NGO),
    ("childfound.or.th", "Children's Foundation Thailand", CAT_NGO),
    ("openforum.or.th", "Open Forum TH", CAT_NGO),
    ("thaihealth.or.th", "ThaiHealth Promotion Foundation", CAT_NGO),
    ("thairra.or.th", "Thai Radio Regulatory Association", CAT_NGO),

    # --- Provincial websites (.go.th) - representative subset ---
    ("bangkok.go.th", "Bangkok Metropolitan Administration", CAT_GOV),
    ("chiangmai.go.th", "Chiang Mai Province", CAT_GOV),
    ("phuket.go.th", "Phuket Province", CAT_GOV),
    ("chonburi.go.th", "Chonburi Province", CAT_GOV),
    ("nakhonratchasima.go.th", "Nakhon Ratchasima Province", CAT_GOV),
    ("khonkaen.go.th", "Khon Kaen Province", CAT_GOV),
    ("songkhla.go.th", "Songkhla Province", CAT_GOV),
    ("ayutthaya.go.th", "Phra Nakhon Si Ayutthaya Province", CAT_GOV),
    ("nonthaburi.go.th", "Nonthaburi Province", CAT_GOV),
    ("pathumthani.go.th", "Pathum Thani Province", CAT_GOV),
    ("samutprakan.go.th", "Samut Prakan Province", CAT_GOV),
    ("samutsakhon.go.th", "Samut Sakhon Province", CAT_GOV),
    ("rayong.go.th", "Rayong Province", CAT_GOV),
    ("chanthaburi.go.th", "Chanthaburi Province", CAT_GOV),
    ("trat.go.th", "Trat Province", CAT_GOV),
    ("prachinburi.go.th", "Prachin Buri Province", CAT_GOV),
    ("nakhonnayok.go.th", "Nakhon Nayok Province", CAT_GOV),
    ("saraburi.go.th", "Saraburi Province", CAT_GOV),
    ("lopburi.go.th", "Lopburi Province", CAT_GOV),
    ("singburi.go.th", "Sing Buri Province", CAT_GOV),
    ("chainat.go.th", "Chai Nat Province", CAT_GOV),
    ("angthong.go.th", "Ang Thong Province", CAT_GOV),
    ("suphanburi.go.th", "Suphan Buri Province", CAT_GOV),
    ("kanchanaburi.go.th", "Kanchanaburi Province", CAT_GOV),
    ("ratchaburi.go.th", "Ratchaburi Province", CAT_GOV),
    ("petchaburi.go.th", "Phetchaburi Province", CAT_GOV),
    ("prachuap.go.th", "Prachuap Khiri Khan Province", CAT_GOV),
    ("nakhonpathom.go.th", "Nakhon Pathom Province", CAT_GOV),
    ("samutsongkhram.go.th", "Samut Songkhram Province", CAT_GOV),
    ("ubonratchathani.go.th", "Ubon Ratchathani Province", CAT_GOV),
    ("yasothon.go.th", "Yasothon Province", CAT_GOV),
    ("amnatcharoen.go.th", "Amnat Charoen Province", CAT_GOV),
    ("nongbualamphu.go.th", "Nong Bua Lamphu Province", CAT_GOV),
    ("udonthani.go.th", "Udon Thani Province", CAT_GOV),
    ("nongkhai.go.th", "Nong Khai Province", CAT_GOV),
    ("loei.go.th", "Loei Province", CAT_GOV),
    ("sakonnakhon.go.th", "Sakon Nakhon Province", CAT_GOV),
    ("nakhonphanom.go.th", "Nakhon Phanom Province", CAT_GOV),
    ("mukdahan.go.th", "Mukdahan Province", CAT_GOV),
    ("kalasin.go.th", "Kalasin Province", CAT_GOV),
    ("roiet.go.th", "Roi Et Province", CAT_GOV),
    ("mahasarakham.go.th", "Maha Sarakham Province", CAT_GOV),
    ("buriram.go.th", "Buri Ram Province", CAT_GOV),
    ("surin.go.th", "Surin Province", CAT_GOV),
    ("sisaket.go.th", "Sisaket Province", CAT_GOV),
    ("chaiyaphum.go.th", "Chaiyaphum Province", CAT_GOV),
    ("petchabun.go.th", "Phetchabun Province", CAT_GOV),
    ("phitsanulok.go.th", "Phitsanulok Province", CAT_GOV),
    ("sukhothai.go.th", "Sukhothai Province", CAT_GOV),
    ("uttaradit.go.th", "Uttaradit Province", CAT_GOV),
    ("phrae.go.th", "Phrae Province", CAT_GOV),
    ("nan.go.th", "Nan Province", CAT_GOV),
    ("phayao.go.th", "Phayao Province", CAT_GOV),
    ("chiangrai.go.th", "Chiang Rai Province", CAT_GOV),
    ("lampang.go.th", "Lampang Province", CAT_GOV),
    ("lamphun.go.th", "Lamphun Province", CAT_GOV),
    ("maehongson.go.th", "Mae Hong Son Province", CAT_GOV),
    ("tak.go.th", "Tak Province", CAT_GOV),
    ("kamphaengphet.go.th", "Kamphaeng Phet Province", CAT_GOV),
    ("nakhonsawan.go.th", "Nakhon Sawan Province", CAT_GOV),
    ("uthaithani.go.th", "Uthai Thani Province", CAT_GOV),
    ("phichit.go.th", "Phichit Province", CAT_GOV),
    ("krabi.go.th", "Krabi Province", CAT_GOV),
    ("pangnga.go.th", "Phang Nga Province", CAT_GOV),
    ("ranong.go.th", "Ranong Province", CAT_GOV),
    ("chumphon.go.th", "Chumphon Province", CAT_GOV),
    ("suratthani.go.th", "Surat Thani Province", CAT_GOV),
    ("nakhonsithammarat.go.th", "Nakhon Si Thammarat Province", CAT_GOV),
    ("phatthalung.go.th", "Phatthalung Province", CAT_GOV),
    ("trang.go.th", "Trang Province", CAT_GOV),
    ("satun.go.th", "Satun Province", CAT_GOV),
    ("pattani.go.th", "Pattani Province", CAT_GOV),
    ("yala.go.th", "Yala Province", CAT_GOV),
    ("narathiwat.go.th", "Narathiwat Province", CAT_GOV),
    ("bueng-kan.go.th", "Bueng Kan Province", CAT_GOV),

    # --- Commerce / e-government services often impersonated ---
    ("krungthai.com", "Krung Thai Bank corporate", CAT_BIZ),

    # --- High-impersonation commercial brands (banks, telecoms, e-wallets) ---
    # These are NOT government domains but they are heavily targeted by Thai
    # phishing campaigns. Including them as whitelist anchors lets the model
    # measure typosquat distance against the impersonated brand.
    ("kasikornbank.com", "Kasikornbank (KBank)", CAT_BIZ),
    ("kbank.co.th", "KBank (legacy)", CAT_BIZ),
    ("kbiz.kasikornbank.com", "K Biz (legacy)", CAT_BIZ),
    ("scb.co.th", "Siam Commercial Bank", CAT_BIZ),
    ("scbeasy.com", "SCB Easy", CAT_BIZ),
    ("bangkokbank.com", "Bangkok Bank", CAT_BIZ),
    ("bbl.co.th", "Bangkok Bank corporate", CAT_BIZ),
    ("krungsri.com", "Krungsri (Bank of Ayudhya)", CAT_BIZ),
    ("kbank-online.kasikornbank.com", "K Online (legacy)", CAT_BIZ),
    ("tmbthanachart.com", "ttb bank", CAT_BIZ),
    ("ttbbank.com", "ttb bank", CAT_BIZ),
    ("uobgroup.com", "UOB Thailand", CAT_BIZ),
    ("uob.co.th", "UOB Thailand", CAT_BIZ),
    ("citibank.co.th", "Citibank Thailand", CAT_BIZ),
    ("hsbc.co.th", "HSBC Thailand", CAT_BIZ),

    # --- Telecoms ---
    ("ais.co.th", "AIS", CAT_BIZ),
    ("dtac.co.th", "DTAC", CAT_BIZ),
    ("truecorp.co.th", "True Corp", CAT_BIZ),
    ("truemoneywallet.com", "TrueMoney Wallet", CAT_BIZ),

    # --- E-commerce / Logistics often impersonated ---
    ("lazada.co.th", "Lazada Thailand", CAT_BIZ),
    ("shopee.co.th", "Shopee Thailand", CAT_BIZ),
    ("kerryexpress.com", "Kerry Express Thailand", CAT_BIZ),
    ("flashexpress.com", "Flash Express", CAT_BIZ),
    ("jtexpress.co.th", "J&T Express", CAT_BIZ),

    # --- Major media (often phished via fake login portals) ---
    ("thairath.co.th", "Thairath", CAT_BIZ),
    ("kapook.com", "Kapook", CAT_BIZ),
    ("sanook.com", "Sanook", CAT_BIZ),
    ("pantip.com", "Pantip", CAT_BIZ),
]


# ---------------------------------------------------------------------------
# Wikipedia enrichment (optional, best-effort).
# ---------------------------------------------------------------------------
_WIKI_PAGES = [
    "https://en.wikipedia.org/wiki/List_of_universities_and_colleges_in_Thailand",
    "https://en.wikipedia.org/wiki/Government_of_Thailand",
    "https://en.wikipedia.org/wiki/List_of_government_ministries_of_Thailand",
]

_DOMAIN_RE = re.compile(
    r"\b([a-z0-9][a-z0-9-]{0,62}(?:\.[a-z0-9][a-z0-9-]{0,62})*\.(?:go|ac|or|co)\.th)\b",
    re.IGNORECASE,
)


def _fetch_wikipedia_domains(timeout: float = 8.0) -> list[tuple[str, str, str]]:
    try:
        import requests
    except Exception:  # noqa: BLE001
        print("[expand] requests unavailable -- skipping wikipedia fetch")
        return []
    out: dict[str, tuple[str, str]] = {}
    for url in _WIKI_PAGES:
        try:
            resp = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": "phish-detector-research/1.0"},
            )
            if not resp.ok:
                print(f"[expand] {url} -> HTTP {resp.status_code}")
                continue
            for match in _DOMAIN_RE.findall(resp.text):
                dom = match.lower()
                # Skip obviously aggregated / decorative paths.
                if dom.startswith(("www.", "th.", "en.")):
                    dom = dom.split(".", 1)[1]
                # Reduce to registrable domain (last 3 labels for *.go.th etc.).
                parts = dom.split(".")
                if len(parts) >= 3:
                    dom = ".".join(parts[-3:])
                tld = dom.rsplit(".", 2)
                if len(tld) < 2:
                    continue
                cat = ".".join(tld[-2:])
                out.setdefault(dom, ("(wikipedia)", cat))
        except Exception as exc:  # noqa: BLE001
            print(f"[expand] {url} failed: {exc}")
    rows = [(dom, name, cat) for dom, (name, cat) in out.items()]
    print(f"[expand] wikipedia contributed {len(rows)} candidate domains")
    return rows


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------
def _load_existing(path: str) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    if not os.path.exists(path):
        return out
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            d = (row.get("domain") or "").strip().lower()
            if not d:
                continue
            out[d] = (
                (row.get("agency_name") or "").strip(),
                (row.get("category") or "other").strip(),
            )
    return out


def _write_csv(path: str, rows: dict[str, tuple[str, str]]) -> None:
    ordered = sorted(rows.items(), key=lambda kv: (kv[1][1], kv[0]))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["domain", "agency_name", "category"])
        for dom, (name, cat) in ordered:
            writer.writerow([dom, name, cat])


def merge(
    existing: dict[str, tuple[str, str]],
    additions: Iterable[tuple[str, str, str]],
) -> dict[str, tuple[str, str]]:
    """Merge ``additions`` into ``existing`` without overwriting curated metadata."""
    out = dict(existing)
    added = 0
    for dom, name, cat in additions:
        dom = dom.strip().lower()
        if not dom or "." not in dom:
            continue
        if dom not in out:
            out[dom] = (name, cat)
            added += 1
    print(f"[expand] +{added} new domains")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Expand the Thai government / education whitelist CSV"
    )
    parser.add_argument(
        "--no-fetch", action="store_true",
        help="skip Wikipedia fetch (curated list only)",
    )
    parser.add_argument(
        "--csv", default=CSV_PATH,
        help="path to thai_gov_domains.csv",
    )
    args = parser.parse_args()

    existing = _load_existing(args.csv)
    print(f"[expand] loaded {len(existing)} existing domains from {args.csv}")

    merged = merge(existing, CURATED_DOMAINS)

    if not args.no_fetch:
        merged = merge(merged, _fetch_wikipedia_domains())

    _write_csv(args.csv, merged)
    print(f"[expand] wrote {len(merged)} domains -> {args.csv}")

    # Quick TLD breakdown for visibility.
    by_cat: dict[str, int] = {}
    for _, cat in merged.values():
        by_cat[cat] = by_cat.get(cat, 0) + 1
    for cat, n in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        print(f"           {cat:>8}: {n}")


if __name__ == "__main__":
    sys.exit(main())
