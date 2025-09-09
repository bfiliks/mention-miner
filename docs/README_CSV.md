Interpreting nodes.csv and edges.csv



These files describe a co-mention network of scholars extracted from your articles.



nodes.csv — one row per scholar (normalized name)



edges.csv — one row per pair of scholars who appear in the same sentence (co-mentions)



By default:



We strip “References/Works Cited/Bibliography” before extraction.



A “co-mention” = two different person names appear in the same sentence at least once.

Multiple mentions in the same sentence count once for that sentence.



Paths you’ll likely use:



Single-article (Kirilloff, large model): data/kirilloff\_big/



Single-article (Kirilloff, small model): data/kirilloff/



Multi-article batch: data/processed/



nodes.csv columns

column	meaning	how to use

name	Normalized person name (after cleaning \& dedup).	This is the node ID.

degree	Number of distinct co-mention partners (neighbors).	“Breadth” of connections. High degree = frequently co-mentioned with many people.

strength	Sum of edge weights incident on the node.	“Intensity” of connections. High strength = repeatedly co-mentioned (even with fewer ppl).

betweenness	Standard betweenness centrality (weighted), 0–1.	Bridge role. High betweenness = connector across subtopics/subfields.

community	Modularity class ID (greedy partition). -1 if isolated / no community.	Color or group nodes by this to see subfields/cliques.

