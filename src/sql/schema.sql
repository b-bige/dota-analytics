--
-- PostgreSQL database dump
--

\restrict SDcxbXO9unxYvV4M5swM3vkYoMGvEG0MyNacCdhGg5waLCBggw9uGRmM6OaMl3z

-- Dumped from database version 17.8 (Debian 17.8-1.pgdg13+1)
-- Dumped by pg_dump version 17.8 (Debian 17.8-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: kaggle; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA kaggle;


ALTER SCHEMA kaggle OWNER TO postgres;

--
-- Name: sync_datetime_human(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.sync_datetime_human() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW."startDateTimeHuman" = TO_TIMESTAMP(NEW."startDateTime");
  NEW."endDateTimeHuman"   = TO_TIMESTAMP(NEW."endDateTime");
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.sync_datetime_human() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: Constants_Leagues; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle."Constants_Leagues" (
    leagueid bigint NOT NULL,
    leaguename text,
    tier text
);


ALTER TABLE kaggle."Constants_Leagues" OWNER TO postgres;

--
-- Name: Constants_Leagues_leagueid_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle."Constants_Leagues_leagueid_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle."Constants_Leagues_leagueid_seq" OWNER TO postgres;

--
-- Name: Constants_Leagues_leagueid_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle."Constants_Leagues_leagueid_seq" OWNED BY kaggle."Constants_Leagues".leagueid;


--
-- Name: Constants_Regions; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle."Constants_Regions" (
    regionid bigint NOT NULL,
    "0" text
);


ALTER TABLE kaggle."Constants_Regions" OWNER TO postgres;

--
-- Name: Constants_Regions_regionid_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle."Constants_Regions_regionid_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle."Constants_Regions_regionid_seq" OWNER TO postgres;

--
-- Name: Constants_Regions_regionid_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle."Constants_Regions_regionid_seq" OWNED BY kaggle."Constants_Regions".regionid;


--
-- Name: draft_timings; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle.draft_timings (
    id bigint NOT NULL,
    "order" bigint,
    pick boolean,
    active_team bigint,
    hero_id bigint,
    player_slot bigint,
    extra_time bigint,
    total_time_taken bigint,
    match_id bigint,
    leagueid bigint
);


ALTER TABLE kaggle.draft_timings OWNER TO postgres;

--
-- Name: draft_timings_id_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle.draft_timings_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle.draft_timings_id_seq OWNER TO postgres;

--
-- Name: draft_timings_id_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle.draft_timings_id_seq OWNED BY kaggle.draft_timings.id;


--
-- Name: main_metadata; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle.main_metadata (
    match_id bigint NOT NULL,
    barracks_status_dire text,
    barracks_status_radiant text,
    cluster bigint,
    dire_score bigint,
    duration bigint,
    engine bigint,
    first_blood_time bigint,
    game_mode bigint,
    human_players bigint,
    leagueid bigint,
    lobby_type bigint,
    match_seq_num bigint,
    negative_votes bigint,
    positive_votes bigint,
    radiant_score bigint,
    radiant_win boolean,
    start_date_time text,
    tower_status_dire text,
    tower_status_radiant text,
    version bigint,
    replay_salt bigint,
    series_id bigint,
    series_type bigint,
    patch bigint,
    region bigint,
    throw bigint,
    loss bigint,
    comeback bigint,
    stomp bigint,
    replay_url text,
    dire_team_id bigint,
    radiant_team_id bigint,
    pre_game_duration bigint,
    flags bigint,
    radiant_logo double precision,
    radiant_team_complete bigint,
    dire_logo double precision,
    dire_team_complete bigint,
    radiant_captain bigint,
    dire_captain bigint,
    average_rank bigint
);


ALTER TABLE kaggle.main_metadata OWNER TO postgres;

--
-- Name: objectives; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle.objectives (
    id bigint NOT NULL,
    "time" bigint,
    type text,
    slot bigint,
    key text,
    player_slot bigint,
    value bigint,
    killer bigint,
    team bigint,
    unit text,
    match_id bigint,
    leagueid bigint
);


ALTER TABLE kaggle.objectives OWNER TO postgres;

--
-- Name: objectives_id_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle.objectives_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle.objectives_id_seq OWNER TO postgres;

--
-- Name: objectives_id_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle.objectives_id_seq OWNED BY kaggle.objectives.id;


--
-- Name: teamfights; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle.teamfights (
    id bigint NOT NULL,
    start bigint,
    "end" bigint,
    last_death bigint,
    deaths bigint,
    players text,
    match_id bigint,
    leagueid bigint
);


ALTER TABLE kaggle.teamfights OWNER TO postgres;

--
-- Name: teamfights_id_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle.teamfights_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle.teamfights_id_seq OWNER TO postgres;

--
-- Name: teamfights_id_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle.teamfights_id_seq OWNED BY kaggle.teamfights.id;


--
-- Name: teams; Type: TABLE; Schema: kaggle; Owner: postgres
--

CREATE TABLE kaggle.teams (
    id bigint NOT NULL,
    match_id bigint,
    leagueid bigint,
    "radiant.team_id" bigint,
    "radiant.name" text,
    "radiant.tag" text,
    "radiant.logo_url" text,
    "dire.team_id" bigint,
    "dire.name" text,
    "dire.tag" text,
    "dire.logo_url" text
);


ALTER TABLE kaggle.teams OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE; Schema: kaggle; Owner: postgres
--

CREATE SEQUENCE kaggle.teams_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE kaggle.teams_id_seq OWNER TO postgres;

--
-- Name: teams_id_seq; Type: SEQUENCE OWNED BY; Schema: kaggle; Owner: postgres
--

ALTER SEQUENCE kaggle.teams_id_seq OWNED BY kaggle.teams.id;


--
-- Name: ability_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ability_details (
    id bigint NOT NULL,
    name text,
    uri text,
    "isTalent" boolean,
    "ability_displayName" text,
    ability_description text,
    "ability_aghanimDescription" text,
    "ability_shardDescription" text,
    type bigint,
    behavior bigint,
    "unitDamageType" bigint,
    "unitTargetType" bigint,
    "unitTargetTeam" bigint,
    "unitTargetFlags" bigint,
    duration text,
    damage text,
    "castPoint" text,
    "castRange" text,
    "channelTime" text,
    "manaCost" text,
    cooldown text,
    "isGrantedByScepter" boolean,
    "isGrantedByShard" boolean,
    "hasScepterUpgrade" boolean,
    "hasShardUpgrade" boolean,
    dispellable text,
    "isInnate" boolean,
    "isUltimate" boolean,
    "linkedAbilityId" bigint
);


ALTER TABLE public.ability_details OWNER TO postgres;

--
-- Name: ability_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ability_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ability_details_id_seq OWNER TO postgres;

--
-- Name: ability_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ability_details_id_seq OWNED BY public.ability_details.id;


--
-- Name: archive_live_match_ids; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.archive_live_match_ids (
    match_id bigint
);


ALTER TABLE public.archive_live_match_ids OWNER TO postgres;

--
-- Name: current_player_ratings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.current_player_ratings (
    account_id bigint NOT NULL,
    mu double precision,
    sigma double precision,
    ordinal double precision,
    last_updated timestamp without time zone
);


ALTER TABLE public.current_player_ratings OWNER TO postgres;

--
-- Name: current_player_ratings_account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.current_player_ratings_account_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.current_player_ratings_account_id_seq OWNER TO postgres;

--
-- Name: current_player_ratings_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.current_player_ratings_account_id_seq OWNED BY public.current_player_ratings.account_id;


--
-- Name: hero_abilities; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_abilities (
    id bigint NOT NULL,
    "heroId" bigint,
    slot bigint,
    "gameVersionId" bigint,
    "abilityId" bigint
);


ALTER TABLE public.hero_abilities OWNER TO postgres;

--
-- Name: hero_abilities_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_abilities_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_abilities_id_seq OWNER TO postgres;

--
-- Name: hero_abilities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_abilities_id_seq OWNED BY public.hero_abilities.id;


--
-- Name: hero_ability_max; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_ability_max (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "abilityId" bigint,
    level bigint,
    "matchCount" bigint,
    "winCount" bigint
);


ALTER TABLE public.hero_ability_max OWNER TO postgres;

--
-- Name: hero_ability_max_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_ability_max_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_ability_max_id_seq OWNER TO postgres;

--
-- Name: hero_ability_max_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_ability_max_id_seq OWNED BY public.hero_ability_max.id;


--
-- Name: hero_ability_min; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_ability_min (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "abilityId" bigint,
    level bigint,
    "matchCount" bigint,
    "winCount" bigint
);


ALTER TABLE public.hero_ability_min OWNER TO postgres;

--
-- Name: hero_ability_min_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_ability_min_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_ability_min_id_seq OWNER TO postgres;

--
-- Name: hero_ability_min_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_ability_min_id_seq OWNED BY public.hero_ability_min.id;


--
-- Name: match_players; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_players (
    match_id bigint,
    "heroId" bigint,
    "isRadiant" boolean,
    "isVictory" boolean,
    variant bigint,
    imp bigint,
    lane text,
    "position" text,
    networth bigint,
    "goldPerMinute" bigint,
    "goldSpent" bigint,
    "towerDamage" bigint,
    "heroDamage" bigint,
    "intentionalFeeding" boolean,
    "steamAccountId" bigint,
    "partyId" text,
    name text,
    "realName" text,
    "profileUri" text,
    "timeCreated" double precision,
    "isAnonymous" boolean,
    "proSteamAccount_teamId" bigint,
    "proSteamAccount_name" text,
    kills smallint,
    deaths smallint,
    assists smallint,
    id bigint NOT NULL
);


ALTER TABLE public.match_players OWNER TO postgres;

--
-- Name: hero_counter_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.hero_counter_stats AS
 SELECT mp1."heroId" AS hero_id,
    mp2."heroId" AS enemy_id,
    avg((mp1."isVictory")::integer) AS winrate,
    count(*) AS games
   FROM (public.match_players mp1
     JOIN public.match_players mp2 ON (((mp1.match_id = mp2.match_id) AND (mp1."isRadiant" <> mp2."isRadiant"))))
  GROUP BY mp1."heroId", mp2."heroId"
 HAVING (count(*) >= 20)
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.hero_counter_stats OWNER TO postgres;

--
-- Name: hero_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_details (
    id bigint NOT NULL,
    name text,
    "displayName" text,
    "shortName" text,
    "gameVersionId" bigint,
    roles jsonb,
    stats jsonb
);


ALTER TABLE public.hero_details OWNER TO postgres;

--
-- Name: hero_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_details_id_seq OWNER TO postgres;

--
-- Name: hero_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_details_id_seq OWNED BY public.hero_details.id;


--
-- Name: hero_facets; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_facets (
    id bigint NOT NULL,
    "heroId" bigint,
    "abilityId" bigint,
    "facetId" bigint,
    slot bigint
);


ALTER TABLE public.hero_facets OWNER TO postgres;

--
-- Name: hero_facets_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_facets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_facets_id_seq OWNER TO postgres;

--
-- Name: hero_facets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_facets_id_seq OWNED BY public.hero_facets.id;


--
-- Name: hero_item_full_purchase; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_item_full_purchase (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "itemId" bigint,
    instance bigint,
    "time" bigint,
    "matchCount" bigint,
    "winCount" bigint,
    "winsAverage" double precision
);


ALTER TABLE public.hero_item_full_purchase OWNER TO postgres;

--
-- Name: hero_item_full_purchase_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_item_full_purchase_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_item_full_purchase_id_seq OWNER TO postgres;

--
-- Name: hero_item_full_purchase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_item_full_purchase_id_seq OWNED BY public.hero_item_full_purchase.id;


--
-- Name: hero_item_starting_purchase; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_item_starting_purchase (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "itemId" bigint,
    instance bigint,
    "wasGiven" boolean,
    "matchCount" bigint,
    "winCount" bigint,
    "winsAverage" double precision
);


ALTER TABLE public.hero_item_starting_purchase OWNER TO postgres;

--
-- Name: hero_item_starting_purchase_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_item_starting_purchase_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_item_starting_purchase_id_seq OWNER TO postgres;

--
-- Name: hero_item_starting_purchase_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_item_starting_purchase_id_seq OWNED BY public.hero_item_starting_purchase.id;


--
-- Name: match_pick_bans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_pick_bans (
    id bigint NOT NULL,
    match_id bigint,
    "isPick" boolean,
    "heroId" bigint,
    "order" bigint,
    "isRadiant" boolean
);


ALTER TABLE public.match_pick_bans OWNER TO postgres;

--
-- Name: hero_pick_ban_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.hero_pick_ban_stats AS
 SELECT count(*) FILTER (WHERE (mpb."isPick" = true)) AS picks,
    count(*) FILTER (WHERE (mpb."isPick" = false)) AS bans,
    hd."displayName"
   FROM (public.match_pick_bans mpb
     JOIN public.hero_details hd ON ((hd.id = mpb."heroId")))
  GROUP BY hd."displayName", hd."shortName"
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.hero_pick_ban_stats OWNER TO postgres;

--
-- Name: hero_presence_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.hero_presence_stats AS
 SELECT count(*) AS presence,
    hd."displayName"
   FROM (public.match_pick_bans mpb
     JOIN public.hero_details hd ON ((hd.id = mpb."heroId")))
  GROUP BY hd."displayName", hd."shortName"
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.hero_presence_stats OWNER TO postgres;

--
-- Name: hero_stats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_stats (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "time" bigint,
    "position" text,
    "bracketBasicIds" text,
    "matchCount" bigint,
    "winCount" bigint,
    networth double precision,
    "goldPerMinute" text,
    "towerDamage" double precision,
    "disableDuration" double precision,
    "disableCount" double precision,
    "stunDuration" double precision,
    "stunCount" double precision,
    "healingSelf" double precision,
    "healingAllies" double precision,
    "heroDamage" double precision,
    "physicalDamage" double precision,
    "magicalDamage" double precision,
    "physicalDamageReceived" double precision,
    "magicalDamageReceived" double precision,
    "supportGold" double precision,
    "campsStacked" double precision
);


ALTER TABLE public.hero_stats OWNER TO postgres;

--
-- Name: hero_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_stats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_stats_id_seq OWNER TO postgres;

--
-- Name: hero_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_stats_id_seq OWNED BY public.hero_stats.id;


--
-- Name: hero_synergy_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.hero_synergy_stats AS
 SELECT LEAST(mp1."heroId", mp2."heroId") AS hero1,
    GREATEST(mp1."heroId", mp2."heroId") AS hero2,
    avg((mp1."isVictory")::integer) AS winrate,
    count(*) AS games
   FROM (public.match_players mp1
     JOIN public.match_players mp2 ON (((mp1.match_id = mp2.match_id) AND (mp1."heroId" < mp2."heroId") AND (mp1."isRadiant" = mp2."isRadiant"))))
  GROUP BY LEAST(mp1."heroId", mp2."heroId"), GREATEST(mp1."heroId", mp2."heroId")
 HAVING (count(*) >= 20)
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.hero_synergy_stats OWNER TO postgres;

--
-- Name: hero_talent; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_talent (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "abilityId" bigint,
    "matchCount" bigint,
    "winCount" bigint,
    "time" bigint,
    "winsAverage" double precision,
    "timeAverage" double precision
);


ALTER TABLE public.hero_talent OWNER TO postgres;

--
-- Name: hero_talent_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_talent_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_talent_id_seq OWNER TO postgres;

--
-- Name: hero_talent_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_talent_id_seq OWNED BY public.hero_talent.id;


--
-- Name: hero_talents; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hero_talents (
    id bigint NOT NULL,
    "heroId" bigint,
    "abilityId" bigint,
    slot bigint
);


ALTER TABLE public.hero_talents OWNER TO postgres;

--
-- Name: hero_talents_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hero_talents_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hero_talents_id_seq OWNER TO postgres;

--
-- Name: hero_talents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hero_talents_id_seq OWNED BY public.hero_talents.id;


--
-- Name: match_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_details (
    id bigint NOT NULL,
    "tournamentId" text,
    "tournamentRound" text,
    "leagueId" bigint,
    "radiantTeamId" bigint,
    "direTeamId" bigint,
    "seriesId" bigint,
    "gameVersionId" bigint,
    "regionId" bigint,
    "clusterId" bigint,
    "didRadiantWin" boolean,
    "startDateTime" bigint,
    "endDateTime" bigint,
    "durationSeconds" bigint,
    "firstBloodTime" bigint,
    "towerStatusRadiant" bigint,
    "towerStatusDire" bigint,
    "barracksStatusRadiant" bigint,
    "barracksStatusDire" bigint,
    rank bigint,
    "actualRank" bigint,
    "averageRank" text,
    "averageImp" bigint,
    bracket bigint,
    "analysisOutcome" text,
    "topLaneOutcome" text,
    "midLaneOutcome" text,
    "bottomLaneOutcome" text,
    "predictedOutcomeWeight" bigint,
    "startDateTimeHuman" timestamp without time zone,
    "endDateTimeHuman" timestamp without time zone,
    avg_radiant_rating double precision,
    avg_dire_rating double precision,
    predicted_radiant_win boolean,
    radiant_score smallint,
    dire_score smallint,
    radiant_draft_score double precision,
    dire_draft_score double precision
);


ALTER TABLE public.match_details OWNER TO postgres;

--
-- Name: hero_winrate_stats; Type: MATERIALIZED VIEW; Schema: public; Owner: postgres
--

CREATE MATERIALIZED VIEW public.hero_winrate_stats AS
 SELECT avg((mp."isVictory")::integer) AS winrate,
    count(*) AS picks,
    hd."displayName"
   FROM ((public.match_players mp
     JOIN public.hero_details hd ON ((mp."heroId" = hd.id)))
     JOIN public.match_details md ON ((mp.match_id = md.id)))
  GROUP BY hd."displayName"
  WITH NO DATA;


ALTER MATERIALIZED VIEW public.hero_winrate_stats OWNER TO postgres;

--
-- Name: item_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.item_details (
    id bigint NOT NULL,
    "shortName" text,
    "displayName" text,
    "isSupportFullItem" text,
    cost bigint,
    "isRecipe" text,
    "isSupport" text,
    behavior bigint,
    "manaCost" text,
    "needsComponents" text,
    "itemResult" bigint,
    quality text,
    attributes jsonb,
    components jsonb,
    image text
);


ALTER TABLE public.item_details OWNER TO postgres;

--
-- Name: item_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.item_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.item_details_id_seq OWNER TO postgres;

--
-- Name: item_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.item_details_id_seq OWNED BY public.item_details.id;


--
-- Name: item_details_opendota; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.item_details_opendota (
    id bigint NOT NULL,
    "shortName" text,
    "displayName" text,
    qual text,
    cost bigint,
    behavior text,
    components text,
    charges text,
    created boolean,
    attributes jsonb
);


ALTER TABLE public.item_details_opendota OWNER TO postgres;

--
-- Name: item_details_opendota_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.item_details_opendota_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.item_details_opendota_id_seq OWNER TO postgres;

--
-- Name: item_details_opendota_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.item_details_opendota_id_seq OWNED BY public.item_details_opendota.id;


--
-- Name: league_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.league_details (
    id bigint NOT NULL,
    "displayName" text,
    "tournamentUrl" text,
    private text,
    "freeToSpectate" text,
    tier text,
    region text,
    "prizePool" bigint,
    "basePrizePool" text,
    "startDateTime" bigint,
    "endDateTime" bigint,
    "lastMatchDate" bigint,
    country text,
    venue text
);


ALTER TABLE public.league_details OWNER TO postgres;

--
-- Name: league_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.league_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.league_details_id_seq OWNER TO postgres;

--
-- Name: league_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.league_details_id_seq OWNED BY public.league_details.id;


--
-- Name: league_node_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.league_node_groups (
    id bigint NOT NULL,
    league_node_id bigint,
    league_id bigint,
    "nodeGroupType" text,
    "secondaryAdvancingTeamCount" text,
    "secondaryAdvancingNodeGroupId" text,
    "tertiaryAdvancingTeamCount" text,
    "tertiaryAdvancingNodeGroupId" text,
    "isFinalGroup" boolean,
    "isTieBreaker" boolean,
    "eliminationDPCPoints" bigint,
    round bigint,
    "maxRounds" bigint,
    "teamCount" bigint,
    "advancingTeamCount" bigint,
    "advancingNodeGroupId" double precision
);


ALTER TABLE public.league_node_groups OWNER TO postgres;

--
-- Name: league_node_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.league_node_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.league_node_groups_id_seq OWNER TO postgres;

--
-- Name: league_node_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.league_node_groups_id_seq OWNED BY public.league_node_groups.id;


--
-- Name: live_matches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.live_matches (
    match_id bigint NOT NULL,
    league_id integer,
    league_name text,
    start_date_time timestamp with time zone,
    radiant_id bigint,
    dire_id bigint,
    radiant_name text,
    dire_name text,
    radiant_logo text,
    dire_logo text,
    radiant_score integer DEFAULT 0,
    dire_score integer DEFAULT 0,
    game_time integer,
    radiant_lead integer,
    last_updated timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_finished boolean,
    status text,
    job_id bigint,
    radiant_draft_score numeric,
    dire_draft_score numeric,
    avg_radiant_rating numeric,
    avg_dire_rating numeric,
    rad_win_predicted double precision
);


ALTER TABLE public.live_matches OWNER TO postgres;

--
-- Name: match_buffs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_buffs (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    "abilityId" bigint,
    "itemId" bigint,
    "stackCount" bigint,
    item_id bigint,
    ability_id text
);


ALTER TABLE public.match_buffs OWNER TO postgres;

--
-- Name: match_buffs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_buffs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_buffs_id_seq OWNER TO postgres;

--
-- Name: match_buffs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_buffs_id_seq OWNED BY public.match_buffs.id;


--
-- Name: match_chat_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_chat_events (
    id bigint NOT NULL,
    match_id bigint,
    "time" bigint,
    type bigint,
    "fromHeroId" bigint,
    "toHeroId" bigint,
    value bigint,
    "pausedTick" bigint,
    "isRadiant" boolean
);


ALTER TABLE public.match_chat_events OWNER TO postgres;

--
-- Name: match_chat_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_chat_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_chat_events_id_seq OWNER TO postgres;

--
-- Name: match_chat_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_chat_events_id_seq OWNED BY public.match_chat_events.id;


--
-- Name: match_courier_kills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_courier_kills (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint
);


ALTER TABLE public.match_courier_kills OWNER TO postgres;

--
-- Name: match_courier_kills_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_courier_kills_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_courier_kills_id_seq OWNER TO postgres;

--
-- Name: match_courier_kills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_courier_kills_id_seq OWNED BY public.match_courier_kills.id;


--
-- Name: match_death_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_death_events (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    attacker bigint,
    "isDieBack" boolean,
    position_x integer,
    position_y integer
);


ALTER TABLE public.match_death_events OWNER TO postgres;

--
-- Name: match_death_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_death_events_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_death_events_id_seq OWNER TO postgres;

--
-- Name: match_death_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_death_events_id_seq OWNED BY public.match_death_events.id;


--
-- Name: match_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_details_id_seq OWNER TO postgres;

--
-- Name: match_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_details_id_seq OWNED BY public.match_details.id;


--
-- Name: match_farm; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_farm (
    farm_id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    source_type text,
    id bigint,
    gold bigint
);


ALTER TABLE public.match_farm OWNER TO postgres;

--
-- Name: match_farm_farm_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_farm_farm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_farm_farm_id_seq OWNER TO postgres;

--
-- Name: match_farm_farm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_farm_farm_id_seq OWNED BY public.match_farm.farm_id;


--
-- Name: match_imp_per_minute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_imp_per_minute (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    imp_per_minute bigint,
    minute smallint
);


ALTER TABLE public.match_imp_per_minute OWNER TO postgres;

--
-- Name: match_imp_per_minute_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_imp_per_minute_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_imp_per_minute_id_seq OWNER TO postgres;

--
-- Name: match_imp_per_minute_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_imp_per_minute_id_seq OWNED BY public.match_imp_per_minute.id;


--
-- Name: match_inventory_reports; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_inventory_reports (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    minute bigint,
    item0_id bigint,
    item1_id bigint,
    item2_id bigint,
    item3_id bigint,
    item4_id bigint,
    item5_id bigint,
    neutral0_id bigint
);


ALTER TABLE public.match_inventory_reports OWNER TO postgres;

--
-- Name: match_inventory_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_inventory_reports_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_inventory_reports_id_seq OWNER TO postgres;

--
-- Name: match_inventory_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_inventory_reports_id_seq OWNED BY public.match_inventory_reports.id;


--
-- Name: match_kills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_kills (
    id bigint NOT NULL,
    match_id bigint,
    radiant_kills bigint,
    dire_kills bigint,
    minute smallint
);


ALTER TABLE public.match_kills OWNER TO postgres;

--
-- Name: match_kills_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_kills_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_kills_id_seq OWNER TO postgres;

--
-- Name: match_kills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_kills_id_seq OWNED BY public.match_kills.id;


--
-- Name: match_leads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_leads (
    id bigint NOT NULL,
    match_id bigint,
    radiant_networth_leads bigint,
    radiant_experience_leads bigint,
    minute smallint
);


ALTER TABLE public.match_leads OWNER TO postgres;

--
-- Name: match_leads_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_leads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_leads_id_seq OWNER TO postgres;

--
-- Name: match_leads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_leads_id_seq OWNED BY public.match_leads.id;


--
-- Name: match_outpost_updates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_outpost_updates (
    id bigint NOT NULL,
    snapshot_id text,
    npc_id bigint,
    is_radiant_controlled boolean,
    is_radiant_side boolean
);


ALTER TABLE public.match_outpost_updates OWNER TO postgres;

--
-- Name: match_outpost_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_outpost_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_outpost_updates_id_seq OWNER TO postgres;

--
-- Name: match_outpost_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_outpost_updates_id_seq OWNED BY public.match_outpost_updates.id;


--
-- Name: match_performance_metrics; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_performance_metrics (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    minute bigint,
    gold_per_minute bigint,
    networth_per_minute bigint,
    experience_per_minute bigint,
    tower_damage_per_minute bigint,
    camp_stack bigint
);


ALTER TABLE public.match_performance_metrics OWNER TO postgres;

--
-- Name: match_performance_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_performance_metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_performance_metrics_id_seq OWNER TO postgres;

--
-- Name: match_performance_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_performance_metrics_id_seq OWNED BY public.match_performance_metrics.id;


--
-- Name: match_pick_bans_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_pick_bans_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_pick_bans_id_seq OWNER TO postgres;

--
-- Name: match_pick_bans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_pick_bans_id_seq OWNED BY public.match_pick_bans.id;


--
-- Name: match_players_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_players_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_players_id_seq OWNER TO postgres;

--
-- Name: match_players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_players_id_seq OWNED BY public.match_players.id;


--
-- Name: match_position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_position (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    minute smallint,
    position_x integer,
    position_y integer
);


ALTER TABLE public.match_position OWNER TO postgres;

--
-- Name: match_position_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_position_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_position_id_seq OWNER TO postgres;

--
-- Name: match_position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_position_id_seq OWNED BY public.match_position.id;


--
-- Name: match_predicted_win_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_predicted_win_rates (
    id bigint NOT NULL,
    match_id bigint,
    predicted_win_rate double precision,
    minute smallint
);


ALTER TABLE public.match_predicted_win_rates OWNER TO postgres;

--
-- Name: match_predicted_win_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_predicted_win_rates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_predicted_win_rates_id_seq OWNER TO postgres;

--
-- Name: match_predicted_win_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_predicted_win_rates_id_seq OWNED BY public.match_predicted_win_rates.id;


--
-- Name: match_purchases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_purchases (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    "itemId" bigint
);


ALTER TABLE public.match_purchases OWNER TO postgres;

--
-- Name: match_purchases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_purchases_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_purchases_id_seq OWNER TO postgres;

--
-- Name: match_purchases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_purchases_id_seq OWNED BY public.match_purchases.id;


--
-- Name: match_runes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_runes (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    rune text,
    action text,
    "positionX" bigint,
    "positionY" bigint
);


ALTER TABLE public.match_runes OWNER TO postgres;

--
-- Name: match_runes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_runes_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_runes_id_seq OWNER TO postgres;

--
-- Name: match_runes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_runes_id_seq OWNED BY public.match_runes.id;


--
-- Name: match_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_snapshots (
    id bigint NOT NULL,
    snapshot_id text,
    match_id bigint,
    order_index bigint
);


ALTER TABLE public.match_snapshots OWNER TO postgres;

--
-- Name: match_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_snapshots_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_snapshots_id_seq OWNER TO postgres;

--
-- Name: match_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_snapshots_id_seq OWNED BY public.match_snapshots.id;


--
-- Name: match_tower_deaths; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_tower_deaths (
    id bigint NOT NULL,
    match_id bigint,
    "time" bigint,
    "npcId" bigint,
    "isRadiant" boolean,
    attacker text
);


ALTER TABLE public.match_tower_deaths OWNER TO postgres;

--
-- Name: match_tower_deaths_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_tower_deaths_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_tower_deaths_id_seq OWNER TO postgres;

--
-- Name: match_tower_deaths_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_tower_deaths_id_seq OWNED BY public.match_tower_deaths.id;


--
-- Name: match_tower_updates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_tower_updates (
    id bigint NOT NULL,
    snapshot_id text,
    npc_id bigint,
    hp bigint
);


ALTER TABLE public.match_tower_updates OWNER TO postgres;

--
-- Name: match_tower_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_tower_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_tower_updates_id_seq OWNER TO postgres;

--
-- Name: match_tower_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_tower_updates_id_seq OWNED BY public.match_tower_updates.id;


--
-- Name: match_ward_destructions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_ward_destructions (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    gold bigint,
    "isWard" boolean
);


ALTER TABLE public.match_ward_destructions OWNER TO postgres;

--
-- Name: match_ward_destructions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_ward_destructions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_ward_destructions_id_seq OWNER TO postgres;

--
-- Name: match_ward_destructions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_ward_destructions_id_seq OWNED BY public.match_ward_destructions.id;


--
-- Name: match_wards; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_wards (
    id bigint NOT NULL,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    type bigint,
    "positionX" numeric,
    "positionY" numeric
);


ALTER TABLE public.match_wards OWNER TO postgres;

--
-- Name: match_wards_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_wards_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_wards_id_seq OWNER TO postgres;

--
-- Name: match_wards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_wards_id_seq OWNED BY public.match_wards.id;


--
-- Name: match_win_rates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.match_win_rates (
    id bigint NOT NULL,
    match_id bigint,
    win_rates double precision,
    minute smallint
);


ALTER TABLE public.match_win_rates OWNER TO postgres;

--
-- Name: match_win_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.match_win_rates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.match_win_rates_id_seq OWNER TO postgres;

--
-- Name: match_win_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.match_win_rates_id_seq OWNED BY public.match_win_rates.id;


--
-- Name: matches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matches (
    match_id bigint NOT NULL,
    duration bigint,
    start_date timestamp without time zone,
    start_time bigint,
    radiant_team_id bigint,
    radiant_name bigint,
    dire_team_id bigint,
    dire_name bigint,
    leagueid bigint,
    league_name bigint,
    series_id bigint,
    series_type bigint,
    radiant_score bigint,
    dire_score bigint,
    radiant_win boolean,
    radiant bigint,
    radiant_team_name text,
    dire_team_name text,
    liquipedia_tier text
);


ALTER TABLE public.matches OWNER TO postgres;

--
-- Name: matches_match_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matches_match_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matches_match_id_seq OWNER TO postgres;

--
-- Name: matches_match_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matches_match_id_seq OWNED BY public.matches.match_id;


--
-- Name: matchup_lane_outcome; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matchup_lane_outcome (
    id bigint NOT NULL,
    "heroId1" bigint,
    "heroId2" bigint,
    week bigint,
    "matchCount" bigint,
    "drawCount" bigint,
    "winCount" bigint,
    "lossCount" bigint,
    "stompWinCount" bigint,
    "stompLossCount" bigint,
    "matchWinCount" bigint,
    "csCount" bigint,
    "position" text
);


ALTER TABLE public.matchup_lane_outcome OWNER TO postgres;

--
-- Name: matchup_lane_outcome_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matchup_lane_outcome_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matchup_lane_outcome_id_seq OWNER TO postgres;

--
-- Name: matchup_lane_outcome_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matchup_lane_outcome_id_seq OWNED BY public.matchup_lane_outcome.id;


--
-- Name: matchup_stats; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matchup_stats (
    id bigint NOT NULL,
    "heroId" bigint,
    week bigint,
    "matchCountWith" bigint,
    "matchCountVs" bigint
);


ALTER TABLE public.matchup_stats OWNER TO postgres;

--
-- Name: matchup_stats_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matchup_stats_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matchup_stats_id_seq OWNER TO postgres;

--
-- Name: matchup_stats_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matchup_stats_id_seq OWNED BY public.matchup_stats.id;


--
-- Name: matchup_vs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matchup_vs (
    id bigint NOT NULL,
    "heroId1" bigint,
    "heroId2" bigint,
    week bigint,
    synergy double precision,
    "winCount" bigint,
    "matchCount" bigint,
    "winsAverage" double precision,
    "goldEarned" bigint,
    xp bigint,
    "heroDamage" bigint,
    "towerDamage" bigint,
    "firstBloodTime" bigint,
    "winRateHeroId1" double precision,
    "winRateHeroId2" double precision
);


ALTER TABLE public.matchup_vs OWNER TO postgres;

--
-- Name: matchup_vs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matchup_vs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matchup_vs_id_seq OWNER TO postgres;

--
-- Name: matchup_vs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matchup_vs_id_seq OWNED BY public.matchup_vs.id;


--
-- Name: matchup_with; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.matchup_with (
    id bigint NOT NULL,
    "heroId1" bigint,
    "heroId2" bigint,
    week bigint,
    synergy double precision,
    "winCount" bigint,
    "matchCount" bigint,
    "winsAverage" double precision,
    "goldEarned" bigint,
    xp bigint,
    "heroDamage" bigint,
    "towerDamage" bigint,
    "firstBloodTime" bigint,
    "winRateHeroId1" double precision,
    "winRateHeroId2" double precision
);


ALTER TABLE public.matchup_with OWNER TO postgres;

--
-- Name: matchup_with_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.matchup_with_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.matchup_with_id_seq OWNER TO postgres;

--
-- Name: matchup_with_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.matchup_with_id_seq OWNED BY public.matchup_with.id;


--
-- Name: npcs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.npcs (
    id bigint NOT NULL,
    name text,
    "statusHealth" double precision,
    "statusHealthRegen" double precision,
    "attackDamageMin" double precision,
    "attackDamageMax" double precision,
    "attackRate" double precision,
    "attackRange" double precision,
    "movementSpeed" double precision,
    "isNeutralUnitType" text,
    "isAncient" text,
    "teamName" text
);


ALTER TABLE public.npcs OWNER TO postgres;

--
-- Name: npcs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.npcs_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.npcs_id_seq OWNER TO postgres;

--
-- Name: npcs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.npcs_id_seq OWNED BY public.npcs.id;


--
-- Name: patches; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patches (
    id bigint NOT NULL,
    name text,
    "asOfDateTime" timestamp without time zone
);


ALTER TABLE public.patches OWNER TO postgres;

--
-- Name: patches_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patches_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patches_id_seq OWNER TO postgres;

--
-- Name: patches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patches_id_seq OWNED BY public.patches.id;


--
-- Name: patches_opendota; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patches_opendota (
    name text,
    date text,
    id bigint NOT NULL
);


ALTER TABLE public.patches_opendota OWNER TO postgres;

--
-- Name: patches_opendota_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patches_opendota_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patches_opendota_id_seq OWNER TO postgres;

--
-- Name: patches_opendota_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patches_opendota_id_seq OWNED BY public.patches_opendota.id;


--
-- Name: team_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_details (
    id bigint NOT NULL,
    name text,
    tag text,
    "dateCreated" text,
    "isPro" text,
    "isLocked" text,
    "countryCode" text,
    "countryName" text,
    url text,
    logo text,
    "baseLogo" text,
    "bannerLogo" text
);


ALTER TABLE public.team_details OWNER TO postgres;

--
-- Name: team_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.team_details_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.team_details_id_seq OWNER TO postgres;

--
-- Name: team_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.team_details_id_seq OWNED BY public.team_details.id;


--
-- Name: team_leagues; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_leagues (
    team_id bigint,
    league_id bigint
);


ALTER TABLE public.team_leagues OWNER TO postgres;

--
-- Name: team_logos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.team_logos (
    team_id bigint,
    logo_url text
);


ALTER TABLE public.team_logos OWNER TO postgres;

--
-- Name: wards_backup; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wards_backup (
    id bigint,
    match_id bigint,
    hero_id bigint,
    "time" bigint,
    type bigint,
    "positionX" bigint,
    "positionY" bigint
);


ALTER TABLE public.wards_backup OWNER TO postgres;

--
-- Name: Constants_Leagues leagueid; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle."Constants_Leagues" ALTER COLUMN leagueid SET DEFAULT nextval('kaggle."Constants_Leagues_leagueid_seq"'::regclass);


--
-- Name: Constants_Regions regionid; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle."Constants_Regions" ALTER COLUMN regionid SET DEFAULT nextval('kaggle."Constants_Regions_regionid_seq"'::regclass);


--
-- Name: draft_timings id; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.draft_timings ALTER COLUMN id SET DEFAULT nextval('kaggle.draft_timings_id_seq'::regclass);


--
-- Name: objectives id; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.objectives ALTER COLUMN id SET DEFAULT nextval('kaggle.objectives_id_seq'::regclass);


--
-- Name: teamfights id; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teamfights ALTER COLUMN id SET DEFAULT nextval('kaggle.teamfights_id_seq'::regclass);


--
-- Name: teams id; Type: DEFAULT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teams ALTER COLUMN id SET DEFAULT nextval('kaggle.teams_id_seq'::regclass);


--
-- Name: ability_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ability_details ALTER COLUMN id SET DEFAULT nextval('public.ability_details_id_seq'::regclass);


--
-- Name: current_player_ratings account_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.current_player_ratings ALTER COLUMN account_id SET DEFAULT nextval('public.current_player_ratings_account_id_seq'::regclass);


--
-- Name: hero_abilities id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_abilities ALTER COLUMN id SET DEFAULT nextval('public.hero_abilities_id_seq'::regclass);


--
-- Name: hero_ability_max id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_ability_max ALTER COLUMN id SET DEFAULT nextval('public.hero_ability_max_id_seq'::regclass);


--
-- Name: hero_ability_min id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_ability_min ALTER COLUMN id SET DEFAULT nextval('public.hero_ability_min_id_seq'::regclass);


--
-- Name: hero_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_details ALTER COLUMN id SET DEFAULT nextval('public.hero_details_id_seq'::regclass);


--
-- Name: hero_facets id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_facets ALTER COLUMN id SET DEFAULT nextval('public.hero_facets_id_seq'::regclass);


--
-- Name: hero_item_full_purchase id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_item_full_purchase ALTER COLUMN id SET DEFAULT nextval('public.hero_item_full_purchase_id_seq'::regclass);


--
-- Name: hero_item_starting_purchase id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_item_starting_purchase ALTER COLUMN id SET DEFAULT nextval('public.hero_item_starting_purchase_id_seq'::regclass);


--
-- Name: hero_stats id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_stats ALTER COLUMN id SET DEFAULT nextval('public.hero_stats_id_seq'::regclass);


--
-- Name: hero_talent id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_talent ALTER COLUMN id SET DEFAULT nextval('public.hero_talent_id_seq'::regclass);


--
-- Name: hero_talents id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_talents ALTER COLUMN id SET DEFAULT nextval('public.hero_talents_id_seq'::regclass);


--
-- Name: item_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_details ALTER COLUMN id SET DEFAULT nextval('public.item_details_id_seq'::regclass);


--
-- Name: item_details_opendota id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_details_opendota ALTER COLUMN id SET DEFAULT nextval('public.item_details_opendota_id_seq'::regclass);


--
-- Name: league_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_details ALTER COLUMN id SET DEFAULT nextval('public.league_details_id_seq'::regclass);


--
-- Name: league_node_groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_node_groups ALTER COLUMN id SET DEFAULT nextval('public.league_node_groups_id_seq'::regclass);


--
-- Name: match_buffs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_buffs ALTER COLUMN id SET DEFAULT nextval('public.match_buffs_id_seq'::regclass);


--
-- Name: match_chat_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_chat_events ALTER COLUMN id SET DEFAULT nextval('public.match_chat_events_id_seq'::regclass);


--
-- Name: match_courier_kills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_courier_kills ALTER COLUMN id SET DEFAULT nextval('public.match_courier_kills_id_seq'::regclass);


--
-- Name: match_death_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_death_events ALTER COLUMN id SET DEFAULT nextval('public.match_death_events_id_seq'::regclass);


--
-- Name: match_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_details ALTER COLUMN id SET DEFAULT nextval('public.match_details_id_seq'::regclass);


--
-- Name: match_farm farm_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_farm ALTER COLUMN farm_id SET DEFAULT nextval('public.match_farm_farm_id_seq'::regclass);


--
-- Name: match_imp_per_minute id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_imp_per_minute ALTER COLUMN id SET DEFAULT nextval('public.match_imp_per_minute_id_seq'::regclass);


--
-- Name: match_inventory_reports id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_inventory_reports ALTER COLUMN id SET DEFAULT nextval('public.match_inventory_reports_id_seq'::regclass);


--
-- Name: match_kills id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_kills ALTER COLUMN id SET DEFAULT nextval('public.match_kills_id_seq'::regclass);


--
-- Name: match_leads id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_leads ALTER COLUMN id SET DEFAULT nextval('public.match_leads_id_seq'::regclass);


--
-- Name: match_outpost_updates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_outpost_updates ALTER COLUMN id SET DEFAULT nextval('public.match_outpost_updates_id_seq'::regclass);


--
-- Name: match_performance_metrics id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_performance_metrics ALTER COLUMN id SET DEFAULT nextval('public.match_performance_metrics_id_seq'::regclass);


--
-- Name: match_pick_bans id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_pick_bans ALTER COLUMN id SET DEFAULT nextval('public.match_pick_bans_id_seq'::regclass);


--
-- Name: match_players id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_players ALTER COLUMN id SET DEFAULT nextval('public.match_players_id_seq'::regclass);


--
-- Name: match_position id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_position ALTER COLUMN id SET DEFAULT nextval('public.match_position_id_seq'::regclass);


--
-- Name: match_predicted_win_rates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_predicted_win_rates ALTER COLUMN id SET DEFAULT nextval('public.match_predicted_win_rates_id_seq'::regclass);


--
-- Name: match_purchases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_purchases ALTER COLUMN id SET DEFAULT nextval('public.match_purchases_id_seq'::regclass);


--
-- Name: match_runes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_runes ALTER COLUMN id SET DEFAULT nextval('public.match_runes_id_seq'::regclass);


--
-- Name: match_snapshots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_snapshots ALTER COLUMN id SET DEFAULT nextval('public.match_snapshots_id_seq'::regclass);


--
-- Name: match_tower_deaths id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_tower_deaths ALTER COLUMN id SET DEFAULT nextval('public.match_tower_deaths_id_seq'::regclass);


--
-- Name: match_tower_updates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_tower_updates ALTER COLUMN id SET DEFAULT nextval('public.match_tower_updates_id_seq'::regclass);


--
-- Name: match_ward_destructions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_ward_destructions ALTER COLUMN id SET DEFAULT nextval('public.match_ward_destructions_id_seq'::regclass);


--
-- Name: match_wards id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_wards ALTER COLUMN id SET DEFAULT nextval('public.match_wards_id_seq'::regclass);


--
-- Name: match_win_rates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_win_rates ALTER COLUMN id SET DEFAULT nextval('public.match_win_rates_id_seq'::regclass);


--
-- Name: matches match_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches ALTER COLUMN match_id SET DEFAULT nextval('public.matches_match_id_seq'::regclass);


--
-- Name: matchup_lane_outcome id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_lane_outcome ALTER COLUMN id SET DEFAULT nextval('public.matchup_lane_outcome_id_seq'::regclass);


--
-- Name: matchup_stats id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_stats ALTER COLUMN id SET DEFAULT nextval('public.matchup_stats_id_seq'::regclass);


--
-- Name: matchup_vs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_vs ALTER COLUMN id SET DEFAULT nextval('public.matchup_vs_id_seq'::regclass);


--
-- Name: matchup_with id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_with ALTER COLUMN id SET DEFAULT nextval('public.matchup_with_id_seq'::regclass);


--
-- Name: npcs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.npcs ALTER COLUMN id SET DEFAULT nextval('public.npcs_id_seq'::regclass);


--
-- Name: patches id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patches ALTER COLUMN id SET DEFAULT nextval('public.patches_id_seq'::regclass);


--
-- Name: patches_opendota id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patches_opendota ALTER COLUMN id SET DEFAULT nextval('public.patches_opendota_id_seq'::regclass);


--
-- Name: team_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_details ALTER COLUMN id SET DEFAULT nextval('public.team_details_id_seq'::regclass);


--
-- Name: Constants_Leagues Constants_Leagues_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle."Constants_Leagues"
    ADD CONSTRAINT "Constants_Leagues_pkey" PRIMARY KEY (leagueid);


--
-- Name: Constants_Regions Constants_Regions_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle."Constants_Regions"
    ADD CONSTRAINT "Constants_Regions_pkey" PRIMARY KEY (regionid);


--
-- Name: draft_timings draft_timings_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.draft_timings
    ADD CONSTRAINT draft_timings_pkey PRIMARY KEY (id);


--
-- Name: objectives objectives_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.objectives
    ADD CONSTRAINT objectives_pkey PRIMARY KEY (id);


--
-- Name: main_metadata pk_main_metadata_match_id; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.main_metadata
    ADD CONSTRAINT pk_main_metadata_match_id PRIMARY KEY (match_id);


--
-- Name: teamfights teamfights_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teamfights
    ADD CONSTRAINT teamfights_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: ability_details ability_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ability_details
    ADD CONSTRAINT ability_details_pkey PRIMARY KEY (id);


--
-- Name: current_player_ratings current_player_ratings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.current_player_ratings
    ADD CONSTRAINT current_player_ratings_pkey PRIMARY KEY (account_id);


--
-- Name: hero_abilities hero_abilities_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_abilities
    ADD CONSTRAINT hero_abilities_pkey PRIMARY KEY (id);


--
-- Name: hero_ability_max hero_ability_max_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_ability_max
    ADD CONSTRAINT hero_ability_max_pkey PRIMARY KEY (id);


--
-- Name: hero_ability_min hero_ability_min_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_ability_min
    ADD CONSTRAINT hero_ability_min_pkey PRIMARY KEY (id);


--
-- Name: hero_details hero_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_details
    ADD CONSTRAINT hero_details_pkey PRIMARY KEY (id);


--
-- Name: hero_facets hero_facets_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_facets
    ADD CONSTRAINT hero_facets_pkey PRIMARY KEY (id);


--
-- Name: hero_item_full_purchase hero_item_full_purchase_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_item_full_purchase
    ADD CONSTRAINT hero_item_full_purchase_pkey PRIMARY KEY (id);


--
-- Name: hero_item_starting_purchase hero_item_starting_purchase_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_item_starting_purchase
    ADD CONSTRAINT hero_item_starting_purchase_pkey PRIMARY KEY (id);


--
-- Name: hero_stats hero_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_stats
    ADD CONSTRAINT hero_stats_pkey PRIMARY KEY (id);


--
-- Name: hero_talent hero_talent_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_talent
    ADD CONSTRAINT hero_talent_pkey PRIMARY KEY (id);


--
-- Name: hero_talents hero_talents_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hero_talents
    ADD CONSTRAINT hero_talents_pkey PRIMARY KEY (id);


--
-- Name: item_details_opendota item_details_opendota_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_details_opendota
    ADD CONSTRAINT item_details_opendota_pkey PRIMARY KEY (id);


--
-- Name: item_details item_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.item_details
    ADD CONSTRAINT item_details_pkey PRIMARY KEY (id);


--
-- Name: league_details league_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_details
    ADD CONSTRAINT league_details_pkey PRIMARY KEY (id);


--
-- Name: league_node_groups league_node_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.league_node_groups
    ADD CONSTRAINT league_node_groups_pkey PRIMARY KEY (id);


--
-- Name: live_matches live_matches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.live_matches
    ADD CONSTRAINT live_matches_pkey PRIMARY KEY (match_id);


--
-- Name: match_buffs match_buffs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_buffs
    ADD CONSTRAINT match_buffs_pkey PRIMARY KEY (id);


--
-- Name: match_chat_events match_chat_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_chat_events
    ADD CONSTRAINT match_chat_events_pkey PRIMARY KEY (id);


--
-- Name: match_courier_kills match_courier_kills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_courier_kills
    ADD CONSTRAINT match_courier_kills_pkey PRIMARY KEY (id);


--
-- Name: match_death_events match_death_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_death_events
    ADD CONSTRAINT match_death_events_pkey PRIMARY KEY (id);


--
-- Name: match_details match_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_details
    ADD CONSTRAINT match_details_pkey PRIMARY KEY (id);


--
-- Name: match_farm match_farm_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_farm
    ADD CONSTRAINT match_farm_pkey PRIMARY KEY (farm_id);


--
-- Name: match_imp_per_minute match_imp_per_minute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_imp_per_minute
    ADD CONSTRAINT match_imp_per_minute_pkey PRIMARY KEY (id);


--
-- Name: match_inventory_reports match_inventory_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_inventory_reports
    ADD CONSTRAINT match_inventory_reports_pkey PRIMARY KEY (id);


--
-- Name: match_kills match_kills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_kills
    ADD CONSTRAINT match_kills_pkey PRIMARY KEY (id);


--
-- Name: match_leads match_leads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_leads
    ADD CONSTRAINT match_leads_pkey PRIMARY KEY (id);


--
-- Name: match_outpost_updates match_outpost_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_outpost_updates
    ADD CONSTRAINT match_outpost_updates_pkey PRIMARY KEY (id);


--
-- Name: match_performance_metrics match_performance_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_performance_metrics
    ADD CONSTRAINT match_performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: match_pick_bans match_pick_bans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_pick_bans
    ADD CONSTRAINT match_pick_bans_pkey PRIMARY KEY (id);


--
-- Name: match_players match_players_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_players
    ADD CONSTRAINT match_players_pkey PRIMARY KEY (id);


--
-- Name: match_position match_position_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_position
    ADD CONSTRAINT match_position_pkey PRIMARY KEY (id);


--
-- Name: match_predicted_win_rates match_predicted_win_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_predicted_win_rates
    ADD CONSTRAINT match_predicted_win_rates_pkey PRIMARY KEY (id);


--
-- Name: match_purchases match_purchases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_purchases
    ADD CONSTRAINT match_purchases_pkey PRIMARY KEY (id);


--
-- Name: match_runes match_runes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_runes
    ADD CONSTRAINT match_runes_pkey PRIMARY KEY (id);


--
-- Name: match_snapshots match_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_snapshots
    ADD CONSTRAINT match_snapshots_pkey PRIMARY KEY (id);


--
-- Name: match_tower_deaths match_tower_deaths_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_tower_deaths
    ADD CONSTRAINT match_tower_deaths_pkey PRIMARY KEY (id);


--
-- Name: match_tower_updates match_tower_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_tower_updates
    ADD CONSTRAINT match_tower_updates_pkey PRIMARY KEY (id);


--
-- Name: match_ward_destructions match_ward_destructions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_ward_destructions
    ADD CONSTRAINT match_ward_destructions_pkey PRIMARY KEY (id);


--
-- Name: match_wards match_wards_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_wards
    ADD CONSTRAINT match_wards_pkey PRIMARY KEY (id);


--
-- Name: match_win_rates match_win_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_win_rates
    ADD CONSTRAINT match_win_rates_pkey PRIMARY KEY (id);


--
-- Name: matches matches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matches
    ADD CONSTRAINT matches_pkey PRIMARY KEY (match_id);


--
-- Name: matchup_lane_outcome matchup_lane_outcome_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_lane_outcome
    ADD CONSTRAINT matchup_lane_outcome_pkey PRIMARY KEY (id);


--
-- Name: matchup_stats matchup_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_stats
    ADD CONSTRAINT matchup_stats_pkey PRIMARY KEY (id);


--
-- Name: matchup_vs matchup_vs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_vs
    ADD CONSTRAINT matchup_vs_pkey PRIMARY KEY (id);


--
-- Name: matchup_with matchup_with_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.matchup_with
    ADD CONSTRAINT matchup_with_pkey PRIMARY KEY (id);


--
-- Name: npcs npcs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.npcs
    ADD CONSTRAINT npcs_pkey PRIMARY KEY (id);


--
-- Name: patches_opendota patches_opendota_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patches_opendota
    ADD CONSTRAINT patches_opendota_pkey PRIMARY KEY (id);


--
-- Name: patches patches_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patches
    ADD CONSTRAINT patches_pkey PRIMARY KEY (id);


--
-- Name: team_details team_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.team_details
    ADD CONSTRAINT team_details_pkey PRIMARY KEY (id);


--
-- Name: idx_did_radiant_win; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_did_radiant_win ON public.match_details USING btree ("didRadiantWin");


--
-- Name: idx_display_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_display_name ON public.league_details USING btree ("displayName");


--
-- Name: idx_hero_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_hero_id ON public.match_players USING btree ("heroId");


--
-- Name: idx_match_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_match_id ON public.match_players USING btree (match_id);


--
-- Name: idx_match_pick_bans_heroid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_match_pick_bans_heroid ON public.match_pick_bans USING btree ("heroId");


--
-- Name: idx_match_players_heroid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_match_players_heroid ON public.match_players USING btree ("heroId");


--
-- Name: idx_match_players_matchid; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_match_players_matchid ON public.match_players USING btree (match_id);


--
-- Name: idx_mpb_matchid_ispick; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mpb_matchid_ispick ON public.match_pick_bans USING btree (match_id, "isPick", "heroId");


--
-- Name: idx_mv_bans; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mv_bans ON public.hero_pick_ban_stats USING btree (bans DESC);


--
-- Name: idx_mv_hero_picks; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mv_hero_picks ON public.hero_winrate_stats USING btree (picks);


--
-- Name: idx_mv_picks; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mv_picks ON public.hero_pick_ban_stats USING btree (picks DESC);


--
-- Name: idx_mv_winrate; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_mv_winrate ON public.hero_winrate_stats USING btree (winrate DESC);


--
-- Name: idx_start_date_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_start_date_time ON public.match_details USING btree ("startDateTimeHuman");


--
-- Name: match_details trg_sync_datetime_human; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_sync_datetime_human BEFORE INSERT OR UPDATE ON public.match_details FOR EACH ROW EXECUTE FUNCTION public.sync_datetime_human();


--
-- Name: draft_timings fk_draft_timings_match_id; Type: FK CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.draft_timings
    ADD CONSTRAINT fk_draft_timings_match_id FOREIGN KEY (match_id) REFERENCES kaggle.main_metadata(match_id) ON DELETE CASCADE;


--
-- Name: objectives fk_objectives_match_id; Type: FK CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.objectives
    ADD CONSTRAINT fk_objectives_match_id FOREIGN KEY (match_id) REFERENCES kaggle.main_metadata(match_id) ON DELETE CASCADE;


--
-- Name: teamfights fk_teamfights_match_id; Type: FK CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teamfights
    ADD CONSTRAINT fk_teamfights_match_id FOREIGN KEY (match_id) REFERENCES kaggle.main_metadata(match_id) ON DELETE CASCADE;


--
-- Name: teams fk_teams_match_id; Type: FK CONSTRAINT; Schema: kaggle; Owner: postgres
--

ALTER TABLE ONLY kaggle.teams
    ADD CONSTRAINT fk_teams_match_id FOREIGN KEY (match_id) REFERENCES kaggle.main_metadata(match_id) ON DELETE CASCADE;


--
-- Name: match_buffs fk_match_buffs_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_buffs
    ADD CONSTRAINT fk_match_buffs_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_chat_events fk_match_chat_events_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_chat_events
    ADD CONSTRAINT fk_match_chat_events_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_courier_kills fk_match_courier_kills_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_courier_kills
    ADD CONSTRAINT fk_match_courier_kills_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_death_events fk_match_death_events_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_death_events
    ADD CONSTRAINT fk_match_death_events_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_farm fk_match_farm_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_farm
    ADD CONSTRAINT fk_match_farm_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_players fk_match_id_match_details; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_players
    ADD CONSTRAINT fk_match_id_match_details FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_imp_per_minute fk_match_imp_per_minute_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_imp_per_minute
    ADD CONSTRAINT fk_match_imp_per_minute_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_inventory_reports fk_match_inventory_reports_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_inventory_reports
    ADD CONSTRAINT fk_match_inventory_reports_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_kills fk_match_kills_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_kills
    ADD CONSTRAINT fk_match_kills_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_leads fk_match_leads_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_leads
    ADD CONSTRAINT fk_match_leads_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_performance_metrics fk_match_performance_metrics_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_performance_metrics
    ADD CONSTRAINT fk_match_performance_metrics_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_pick_bans fk_match_pick_bans_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_pick_bans
    ADD CONSTRAINT fk_match_pick_bans_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_predicted_win_rates fk_match_predicted_win_rates_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_predicted_win_rates
    ADD CONSTRAINT fk_match_predicted_win_rates_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_purchases fk_match_purchases_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_purchases
    ADD CONSTRAINT fk_match_purchases_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_runes fk_match_runes_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_runes
    ADD CONSTRAINT fk_match_runes_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_snapshots fk_match_snapshots_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_snapshots
    ADD CONSTRAINT fk_match_snapshots_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_tower_deaths fk_match_tower_deaths_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_tower_deaths
    ADD CONSTRAINT fk_match_tower_deaths_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_ward_destructions fk_match_ward_destructions_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_ward_destructions
    ADD CONSTRAINT fk_match_ward_destructions_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_wards fk_match_wards_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_wards
    ADD CONSTRAINT fk_match_wards_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_win_rates fk_match_win_rates_match_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_win_rates
    ADD CONSTRAINT fk_match_win_rates_match_id FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- Name: match_position match_position_match_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.match_position
    ADD CONSTRAINT match_position_match_id_fkey FOREIGN KEY (match_id) REFERENCES public.match_details(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict SDcxbXO9unxYvV4M5swM3vkYoMGvEG0MyNacCdhGg5waLCBggw9uGRmM6OaMl3z

