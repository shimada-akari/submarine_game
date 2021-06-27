cd /Users/shimada_akari/biology/Sclass/programing_practice/submarine-py


for i in $(seq 3)
do
    echo $i
    ruby source/server.rb 2000 &
    sleep 1
    python3 players/random_player.py localhost 2000 &
    sleep 1
    python3 players/player_1.py localhost 2000 
    sleep 1
done

