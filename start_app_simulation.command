cd /Users/shimada_akari/biology/Sclass/programing_practice/submarine_game


for i in $(seq 30)
do
    echo $i
    ruby source/server.rb 2000 $i &
    sleep 1
    python3 players/random_player.py localhost 2000 --seed $(($i)) &
    sleep 1
    python3 players/random_player_2.py localhost 2000 --seed $(($i+1))
    sleep 1
done

