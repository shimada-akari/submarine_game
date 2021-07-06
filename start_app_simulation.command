cd /Users/shimada_akari/biology/Sclass/programing_practice/submarine_game

player_1='random_player_1.py'
player_2='random_player_2.py'

echo player1: $player_1, player2: $player_2 >> result.txt

for i in $(seq 30)
do
    echo $i
    ruby source/server.rb 2000 $i &
    sleep 1
    python3 players/$player_1 localhost 2000 --seed $(($i)) &
    sleep 1
    python3 players/$player_2 localhost 2000 --seed $(($i+1))
    sleep 2
done

