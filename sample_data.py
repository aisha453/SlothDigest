"""
sample_data.py - Built-in realistic chat presets for instant 1-click testing.
"""

SAMPLE_PRESETS = {
    "🍕 Dinner Debate (Green - 47 Messages)": {
        "description": "Friends spending 45 minutes arguing over where to eat. A chaotic back-and-forth about dietary restrictions, traffic, and indecision. You were not tagged.",
        "text": """[6:15 PM] Dave: Anyone hungry tonight?
[6:16 PM] Sarah: Starving. What are we thinking?
[6:17 PM] Mike: Thai? Pad Thai sounds amazing.
[6:18 PM] Sarah: Had Thai yesterday for lunch... sushi?
[6:19 PM] Chloe: Sushi is so expensive though. And parking downtown is a nightmare.
[6:21 PM] Dave: What about that new burger place on 4th street?
[6:22 PM] Mike: I'm cutting carbs this week guys, remember?
[6:23 PM] Chloe: Burgers without buns are depressing Mike.
[6:25 PM] Dave: Ok, pizza?
[6:26 PM] Sarah: Mike just said he's cutting carbs! 🤦‍♀️
[6:27 PM] Mike: Look I can eat a salad if you guys really want pizza, it's fine...
[6:29 PM] Chloe: Don't be a martyr Mike. What about Mexican?
[6:30 PM] Dave: Los Amigos?
[6:31 PM] Sarah: Los Amigos is closed on Mondays!
[6:32 PM] Dave: Today is Wednesday Sarah.
[6:33 PM] Sarah: Oh. Right. Time has no meaning.
[6:35 PM] Mike: Tacos work for me! Carnitas has protein.
[6:36 PM] Chloe: Can we get a table for 5 at 8 PM?
[6:38 PM] Dave: I just called them, 8 PM is reserved under 'Dave'.
[6:39 PM] Sarah: Perfect. See you all at Los Amigos at 8!
[6:40 PM] Mike: 👍
[6:41 PM] Chloe: 🎉"""
    },
    "🚨 Friday 4:45 PM Slack Emergency (Yellow/Green)": {
        "description": "A classic panic in the #engineering Slack channel over an automated memory spike alert that auto-resolved.",
        "text": """[4:46 PM] [BOT-Datadog]: ⚠️ ALERT: Worker node-prod-04 memory utilization > 89% for 5m.
[4:47 PM] Alex (Junior Dev): Oh god, is production down?! Should I page on-call?
[4:48 PM] Alex: Seeing elevated response times on /api/v1/checkout maybe?
[4:49 PM] Priya: Checking now... checkout looks green on my dashboard.
[4:51 PM] Alex: Wait, the memory is at 91% now!! Should we restart the container pods?
[4:52 PM] Priya: DON'T restart pods during peak traffic! Let's check the logs first.
[4:54 PM] Marcus (Staff Engineer): Relax everyone. Today is the 15th. The bi-weekly batch billing reconciliation cron job runs at 4:45 PM. It spikes worker-04 memory every single time for 8 minutes and then dumps cache.
[4:56 PM] [BOT-Datadog]: ✅ RESOLVED: Worker node-prod-04 memory utilization normalized to 34%.
[4:57 PM] Alex: Oh... whew. Sorry for the false alarm! 😅
[4:58 PM] Priya: Haha no worries Alex, good vigilance! Have a good weekend all!
[4:59 PM] Marcus: Closing laptop. Don't touch anything until Monday."""
    },
    "🏡 Neighborhood HOA Lawn Gnome War (Yellow - Petty Drama)": {
        "description": "Suburban neighborhood WhatsApp group erupting over an unauthorized garden gnome and lawn care rules.",
        "text": """[8:12 AM] Brenda (Unit 12): Good morning neighbors. I would like to remind everyone that Section 4.2 of the HOA bylaws clearly states decorative lawn fixtures exceeding 12 inches require prior board review.
[8:15 AM] Tom (Unit 14): Are you seriously talking about my garden gnome Brenda? It's a gnome holding a solar flashlight.
[8:18 AM] Brenda: The bylaws exist to preserve our neighborhood aesthetic Tom. It's garish and shines directly into my living room at dusk.
[8:21 AM] Janet (Unit 7): Honestly I think the little guy is cute. His name is Barnaby.
[8:22 AM] Tom: Thank you Janet. Barnaby stays.
[8:25 AM] Brenda: I will be tabling a formal grievance motion at the next quarterly meeting on November 12th.
[8:27 AM] Rick (Unit 3): Can we please not do this on the emergency announcements group? Some of us work night shifts.
[8:30 AM] Brenda: Fine. See you all at the November 12 meeting."""
    }
}
