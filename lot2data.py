# -*- coding: utf-8 -*-

#Hardcoded data. Various fields that are needed for other functions
#Lists of stats, characters, and subclasses.
#It's bulky and best kept out of sight in this file.

#(Short names)
#This is now in titles.csv...
character_ids = {
    1  : 'Reimu',
    2  : 'Marisa',
    3  : 'Rinnosuke',
    4  : 'Keine',
    5  : 'Momiji',
    6  : 'Youmu',
    7  : 'Kogasa',
    8  : 'Rumia',
    9  : 'Cirno',
    10 : 'Minoriko',
    11 : 'Komachi',
    12 : 'Chen',
    13 : 'Nitori',
    14 : 'Parsee',
    15 : 'Wriggle',
    16 : 'Kaguya',
    17 : 'Mokou',
    18 : 'Aya',
    19 : 'Mystia',
    20 : 'Kasen',
    21 : 'Nazrin',
    22 : 'Hina',
    23 : 'Rin',
    24 : 'Utsuho',
    25 : 'Satori',
    26 : 'Yuugi',
    27 : 'Meiling',
    28 : 'Alice',
    29 : 'Patchouli',
    30 : 'Eirin',
    31 : 'Reisen',
    32 : 'Sanae',
    33 : 'Iku',
    34 : 'Suika',
    35 : 'Ran',
    36 : 'Remilia',
    37 : 'Sakuya',
    38 : 'Kanako',
    39 : 'Suwako',
    40 : 'Tenshi',
    41 : 'Flandre',
    42 : 'Yuyuko',
    43 : 'Yuuka',
    44 : 'Yukari',
    45 : 'Byakuren',
    46 : 'Shiki',
    47 : 'Renko',
    48 : 'Maribel',
    49 : 'Shou',
    50 : 'Mamizou',
    51 : 'Futo',
    52 : 'Miko',
    53 : 'Kokoro',
    54 : 'Tokiko',
    55 : 'Koishi',
    56 : 'Akyuu',
}
character_lookup = {character_ids[i]:i for i in character_ids}

subclasses = {
    0   : "None",
    100 : "Guardian",
    101 : "Monk",
    102 : "Warrior",
    103 : "Sorcerer",
    104 : "Healer",
    105 : "Enhancer",
    106 : "Hexer",
    107 : "Toxicologist",
    108 : "Magician",
    109 : "Herbalist",
    110 : "Strategist",
    111 : "Gambler",
    112 : "Diva",
    113 : "Transcendent",
    114 : "Swordmaster",
    115 : "Archmage",
    116 : "Appraiser",
    117 : "Elementalist",
    118 : "Ninja",
    119 : "Oracle",
    120 : "Holy Blessing",
    121 : "Dragon God's Power",
    122 : "WINNER",
}

#Level-up bonuses and library skill levels
#Also the list of stats that have growth rates.
stats = [
    'HP',
    'ATK',
    'DEF',
    'MAG',
    'MND',
    'SPD',
]
affinities = [
    'FIR',
    'CLD',
    'WND',
    'NTR',
    'MYS',
    'SPI',
    'DRK',
    'PHY',
]
#(and void, but you can't raise that.)
resistances = [
    'PSN',
    'PAR',
    'HVY',
    'SHK',
    'TRR',
    'SIL',
    'DTH',
    'DBF',  #At least for monsters this is 5+ separate stats but I don't know if this is true for players. It's never shown as such.
]

#stats that can be boosted by a gem.
gem_stats = [
    'HP',
    'MP',
    'TP',
    'ATK',
    'DEF',
    'MAG',
    'MND',
    'SPD',
]
#Stats that can be boosted by a skill. Also skills that can be unlocked by an item.
boost_stats = [
    'HP',
    'MP',
    'TP',
    'ATK',
    'DEF',
    'MAG',
    'MND',
    'SPD',
    'EVA',
    'ACC',
    'AFF',  #Affinities
    'RES',  #(status) Resistances
]

monster_types = [
    'HUM',
    'YOU',
    'GST',
    'PNT',  #Plant
    'BST',
    'FLY',
    'INS',  #Insect
    'AQA',  #Aquatic
    'INO',  #Inorganic
    'ONI',
    'DRG',
    'DVN',  #Divine
    'OTH',  #Other
]

#Note - Boost2 skills aren't available for the last 4. This list is coincidentally the same as gem_stats
boost_2_stats = gem_stats

#Lookup stat name to index in the array
stat_index = {boost_stats[i]:i for i in range(len(boost_stats))}

SKILL_COUNT = 40
SUBCLASS_SKILL_COUNT = 20
