MATCH_IS_PARSED = """
    query($id: Long!) {
        match(id: $id) {
            id
            parsedDateTime
        }
    }
"""

MATCH_DETAIL_QUERY = """
    query($id: Long!) {
        match(id: $id) {
            id
            tournamentId
            tournamentRound
            leagueId
            radiantTeamId
            direTeamId
            seriesId
            gameVersionId
            regionId
            clusterId
            didRadiantWin
            startDateTime
            endDateTime
            durationSeconds
            firstBloodTime
            towerStatusRadiant
            towerStatusDire
            barracksStatusRadiant
            barracksStatusDire
            rank
            actualRank
            averageRank
            averageImp
            bracket
            analysisOutcome
            topLaneOutcome
            midLaneOutcome
            bottomLaneOutcome
            predictedOutcomeWeight
            pickBans {
                isPick
                heroId
                order
                isRadiant
            }
            chatEvents {
                time
                type
                fromHeroId
                toHeroId
                value
                pausedTick
                isRadiant
            }
            predictedWinRates
            winRates
            radiantNetworthLeads
            radiantExperienceLeads
            radiantKills
            direKills
            towerDeaths {
                time
                npcId
                isRadiant
                attacker
            }
            towerStatus {
                towers {
                    npcId
                    hp
                }
            outposts {
                npcId
                isControlledByRadiant
                isRadiantSide
            }
        }
        players {
        heroId
        steamAccountId
        partyId
        steamAccount {
            name
            realName
            profileUri
            timeCreated
            isAnonymous
            proSteamAccount {
                teamId
                name
            }
        }
        kills
        deaths
        assists
        isRadiant
        isVictory
        variant
        imp
        lane
        position
        networth
        goldPerMinute
        goldSpent
        towerDamage
        heroDamage
        intentionalFeeding
        stats {
            impPerMinute
            goldPerMinute
            networthPerMinute
            experiencePerMinute
            towerDamagePerMinute
            campStack
            locationReport {
            positionX
            positionY
            }
            deathEvents {
            time
            attacker
            isDieBack
            positionX
            positionY
            }
            farmDistributionReport {
            creepLocation {
                id
                gold
            }
            neutralLocation {
                id
                gold
            }
            ancientLocation {
                id
                gold
            }
            buildings {
                id
                gold
            }
            bountyGold {
                id
                gold
            }
            other {
                id
                gold
            }
            buyBackGold
            }
            matchPlayerBuffEvent {
            time
            abilityId
            itemId
            stackCount
            }
            inventoryReport {
            item0 {
                itemId
            }
            item1 {
                itemId
            }
            item2 {
                itemId
            }
            item3 {
                itemId
            }
            item4 {
                itemId
            }
            item5 {
                itemId
            }
            neutral0 {
                itemId
            }
            }
            itemPurchases {
            time
            itemId
            }
            courierKills {
            time
            }
            runes {
            time
            rune
            action
            positionX
            positionY
            }
            wards {
            time
            type
            positionX
            positionY
            }
            wardDestruction {
            time
            gold
            isWard
            }
        }
        }
    }
    }
"""