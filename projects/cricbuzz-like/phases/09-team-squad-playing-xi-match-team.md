# Phase 09 — Team, Squad, Playing XI, MatchTeam & MatchPlayer Modelling

## Goal

Model team participation correctly for a specific match.

The key problem is:

> A global Team is not the same thing as that Team participating in one specific Match.

And:

> A Player is not globally a striker, captain, wicketkeeper, or selected XI member.

Those are context-specific roles.

---

## 1. Why `Team.players` is not enough

A naive design:

```python
class Team:
    def __init__(self, name, players):
        self.name = name
        self.players = players
```

looks reasonable, but it mixes several different ideas:

```text
Permanent team identity
Current squad
Playing XI
Captain
Wicketkeeper
Match-specific selection
```

A team can have different selections across matches.

Example:

```text
India vs Australia — Match 1
Playing XI = A

India vs Australia — Match 2
Playing XI = B
```

So Playing XI does not belong directly to global Team.

---

## 2. Global Team vs Match-specific Team

Global entity:

```text
Team
----
id
name
country
```

Match-specific participation:

```text
MatchTeam
---------
match
team
squad
playing_xi
captain
wicketkeeper
```

So:

```text
Team
    |
    | participates as
    v
MatchTeam
    |
    v
Match
```

`MatchTeam` represents:

> this Team inside this Match.

---

## 3. Why MatchTeam deserves its own class

The relationship between Match and Team has data.

For example:

```text
captain
wicketkeeper
squad
playing XI
possibly innings order
```

General modelling rule:

> If a relationship has important state or behavior, promote the relationship into a domain object.

Other examples:

```text
Student + Course → Enrollment
User + Project → ProjectMembership
Product + Order → OrderItem
```

For Cricbuzz:

```text
Match + Team → MatchTeam
```

---

## 4. Squad vs Playing XI

These are different concepts.

Squad:

```text
all players selected/registered for the match context
```

Playing XI:

```text
players actually selected to play
```

Example:

```text
Squad = 15 players
Playing XI = 11 players
```

So:

```text
MatchTeam
   |
   +-- Squad
   |
   +-- PlayingXI
```

Do not treat them as the same list.

---

## 5. Player vs MatchPlayer

Global Player:

```text
Player
------
id
name
date_of_birth
country
playing_role
```

But match-specific information may include:

```text
selected
captain
wicketkeeper
substitute
starting batter
```

That suggests a context object such as:

```text
MatchPlayer
```

or:

```text
SquadPlayer
```

Conceptually:

```text
Player
   |
   | wrapped in match context
   v
MatchPlayer
```

---

## 6. Why not put captain on Player?

Bad:

```python
player.is_captain = True
```

Why bad?

Because captaincy is contextual.

A player can be:

```text
captain in Match A
not captain in Match B
```

Same with wicketkeeper.

Therefore:

```text
captain
wicketkeeper
selected
```

should usually belong to the match participation context, not global Player.

---

## 7. First rough model

```python
class Player:
    def __init__(self, player_id, name):
        self.id = player_id
        self.name = name


class Team:
    def __init__(self, team_id, name):
        self.id = team_id
        self.name = name
```

Now match-specific player:

```python
class MatchPlayer:
    def __init__(
        self,
        player,
        is_captain=False,
        is_wicketkeeper=False,
        is_selected=False,
    ):
        self.player = player
        self.is_captain = is_captain
        self.is_wicketkeeper = is_wicketkeeper
        self.is_selected = is_selected
```

And MatchTeam:

```python
class MatchTeam:
    def __init__(self, team, squad):
        self.team = team
        self.squad = squad
```

---

## 8. Better modelling: make Playing XI explicit

Instead of relying only on `is_selected`, we can keep a separate collection:

```python
class MatchTeam:

    def __init__(self, team):
        self.team = team
        self.squad = []
        self.playing_xi = []
        self.captain = None
        self.wicketkeeper = None
```

This makes domain intent clearer.

Then:

```python
def add_to_squad(self, player):
    ...

def select_playing_xi(self, players):
    ...

def assign_captain(self, player):
    ...

def assign_wicketkeeper(self, player):
    ...
```

---

## 9. Invariants MatchTeam should protect

Examples:

```text
Playing XI must be selected from squad.
Captain must be in Playing XI.
Wicketkeeper must be in Playing XI.
No duplicate player in squad.
No duplicate player in Playing XI.
Playing XI size must satisfy match rules.
```

These are excellent reasons for MatchTeam to own behavior.

---

## 10. Example implementation

```python
class MatchTeam:

    def __init__(self, team):
        self.team = team
        self.squad = []
        self.playing_xi = []
        self.captain = None
        self.wicketkeeper = None

    def add_to_squad(self, player):
        if player in self.squad:
            raise ValueError("Player already in squad")

        self.squad.append(player)

    def select_playing_xi(self, players):
        if any(
            player not in self.squad
            for player in players
        ):
            raise ValueError(
                "Playing XI must come from squad"
            )

        if len(set(players)) != len(players):
            raise ValueError(
                "Duplicate player in Playing XI"
            )

        self.playing_xi = list(players)

    def assign_captain(self, player):
        if player not in self.playing_xi:
            raise ValueError(
                "Captain must be in Playing XI"
            )

        self.captain = player

    def assign_wicketkeeper(self, player):
        if player not in self.playing_xi:
            raise ValueError(
                "Wicketkeeper must be in Playing XI"
            )

        self.wicketkeeper = player
```

---

## 11. Where does MatchPlayer fit?

There are two valid modelling choices.

### Option A — simple collections

```text
MatchTeam
  squad: list[Player]
  playing_xi: list[Player]
  captain: Player
  wicketkeeper: Player
```

This is enough when player-specific match metadata is small.

### Option B — explicit MatchPlayer entity/value structure

```text
MatchTeam
  |
  +-- MatchPlayer
        |
        +-- Player
        +-- selected
        +-- captain
        +-- wicketkeeper
        +-- substitute
```

Use this when match-specific player metadata grows.

Important rule:

> Do not create MatchPlayer just because it sounds more object-oriented.

Create it when the relationship has enough state/behavior to justify it.

---

## 12. Recommended current design

For our current LLD:

```text
Player
Team

Match
  |
  +-- MatchTeam A
  |     |
  |     +-- Team
  |     +-- Squad
  |     +-- PlayingXI
  |     +-- captain
  |     +-- wicketkeeper
  |
  +-- MatchTeam B
```

We can introduce MatchPlayer later if we need richer match-specific player state.

---

## 13. Why Team should not own MatchTeam

`MatchTeam` belongs to a Match context.

So lifecycle ownership is closer to:

```text
Match
  ◆── MatchTeam
        ---- Team
```

Meaning:

```text
Match owns MatchTeam
MatchTeam references global Team
```

The global Team does not disappear when MatchTeam disappears.

---

## 14. Cardinality

Conceptually:

```text
Match 1 -------- 2 MatchTeam
MatchTeam N ---- 1 Team
MatchTeam 1 ---- N Player (squad)
MatchTeam 1 ---- N Player (Playing XI)
```

At the global level:

```text
Team N ---- M Player
```

but match selection is contextual.

---

## 15. Why direct Many-to-Many can be misleading

Database design might tempt us to create:

```text
match_teams
match_players
```

But LLD should first capture meaning.

The important domain concept is:

```text
MatchTeam
```

because the relationship has behavior and invariants.

Then persistence can map it however is practical.

---

## 16. Batter / bowler / striker are roles, not identities

A Player can become:

```text
striker
non-striker
bowler
fielder
```

during different deliveries.

Do not create global classes:

```text
Striker
Bowler
NonStriker
```

unless they truly own distinct behavior/state.

Usually:

```text
Delivery.striker → Player
Delivery.non_striker → Player
Delivery.bowler → Player
```

is enough.

---

## 17. MatchTeam behavior examples

Useful methods:

```text
add_to_squad()
select_playing_xi()
assign_captain()
assign_wicketkeeper()
contains_player()
is_playing_member()
```

Example:

```python
def is_playing_member(self, player):
    return player in self.playing_xi
```

Then Innings can validate:

```python
if not batting_match_team.is_playing_member(striker):
    raise InvalidPlayer()
```

This keeps selection rules close to MatchTeam.

---

## 18. Where match format rules can participate

Playing XI size may be fixed at 11 for standard cricket, but we should avoid hard-coding broader format assumptions everywhere.

A rule strategy could validate:

```python
rules.validate_playing_xi(players)
```

Then MatchTeam focuses on ownership while MatchRules handles format-specific constraints if needed.

---

## 19. Aggregate boundary thinking

External code should not do:

```python
match_team.playing_xi.append(player)
```

because that bypasses invariants.

Prefer:

```python
match_team.select_playing_xi(players)
```

Likewise:

```python
match_team.assign_captain(player)
```

This preserves consistency.

---

## 20. Example setup flow

```text
Create Match
   ↓
Attach Team A / Team B
   ↓
Create MatchTeam for each
   ↓
Add squad members
   ↓
Select Playing XI
   ↓
Assign captain
   ↓
Assign wicketkeeper
   ↓
Record toss
```

This is much closer to the real domain lifecycle than storing everything directly on Team.

---

## 21. Interview explanation

A strong answer:

> I would keep Player and Team as global entities. Match-specific participation would be represented by MatchTeam because the Match–Team relationship contains squad, Playing XI, captain and wicketkeeper information. Match owns MatchTeam, while MatchTeam references the global Team. I would introduce MatchPlayer only if player-level match metadata becomes rich enough to justify its own object.

---

## Key takeaway

```text
Global identity:
Player
Team

Match context:
MatchTeam
Squad
PlayingXI

Temporary roles:
striker
non-striker
bowler
captain
wicketkeeper
```

Do not place context-specific state on global entities.
