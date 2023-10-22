"""
This module contains the configurations for Secret Hitler games. Games vary\
in structure depending on the number of players in the game.
"""

configuration = {
    5: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": True
    },

    6: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": True
    },

    7: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": False
    },

    8: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": False
    },

    9: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Fascist',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": False
    },

    10: {
        "roles": [
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Liberal',
            'Fascist',
            'Fascist',
            'Fascist',
            'Hitler'
        ],
        "Hitler_knows_fascists": False
    }
}