import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip


class Player_2(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        # フィールドを2x2の配列として持っている．
        self.field = [[i, j] for i in range(Player.FIELD_SIZE)
                      for j in range(Player.FIELD_SIZE)]

        # 初期配置を非復元抽出でランダムに決める．
        ps = random.sample(self.field, 3)
        positions = {'w': ps[0], 'c': ps[1], 's': ps[2]}
        super().__init__(positions)

    #
    # 移動か攻撃かランダムに決める．
    # どれがどこへ移動するか，あるいはどこに攻撃するかもランダム．
    #
    def action(self, past_result):
        
        if "result" not in past_result: #まだ相手が攻撃/移動をしていない
            # print("result not fount.")
            act = "attack"
        
        else:
            past_result = eval(past_result)
            print(past_result)

            if "attacked" in past_result["result"]:
                
                past_attacked = past_result["result"]["attacked"]
                #moveを選択するとき：hitかつhitされた船が残っている または nearがある

                # print("past_attacked[near] != []", past_attacked["near"] != [])

                if "hit" in past_attacked: 
                    my_ships = past_result["condition"]["me"]
                    if past_attacked["hit"] in my_ships: #hitかつhitされた船が残っている
                        #past_attacked["hit"] : hitされた船の名前( "s" )が返ってくる
                        #hitされた船を移動させる。（第一優先）
                        print("attacked hit.")
                        act = "move"
                        ship_name = past_attacked["hit"]
                        

                    else: #hitで船が無くなった
                        if past_attacked["near"] != []: #hitで船が無くなった かつ nearで位置がバレそうな船がある。
                            near_ships = past_attacked["near"]
                            act = "move"
                            near_ships_hp = {}
                            ships_hp_position = past_result["condition"]["me"] #{'w': {'hp': 3, 'position': [2, 1]}
                            
                            for s_name in near_ships:
                                near_ships_hp[s_name] = ships_hp_position[s_name]["hp"]
                        
                            ship_name = min(near_ships_hp) #nearで場所がバレた船のうち、一番hpが少ないものの名前

                        else:
                            print("lost ship by hit.")
                            act = "attack"

                elif past_attacked["near"] != []: #hitされた船はないが、nearで位置がバレそうな船がある。
                    #nearであげられた船の1つを移動させる。（第二優先）<-nearで複数の船があげられたとき、どの船を優先的に動かすべきか？？ 
                    #一番hpが少ないものを移動させる。
                    print("attacked near.")
                    act = "move"
                    ships = past_attacked["near"]
                    ships_hp_position = past_result["condition"]["me"] #{'w': {'hp': 3, 'position': [2, 1]}
                    
                    near_ships_hp = {}
                    for s_name in ships:
                        near_ships_hp[s_name] = ships_hp_position[s_name]["hp"]
                
                    ship_name = min(near_ships_hp) #nearで場所がバレた船のうち、一番hpが少ないものの名前
                
                else: #attackedでhit/nearがなかった
                    print("attacked but safe.")
                    act = "attack"

            else: #相手の行動がmovedのとき
                print("moved.")
                act = "attack"

        print("choice : ", act)

        # act = random.choice(["move", "attack"])

        if act == "move":
            # ship = random.choice(list(self.ships.values()))
            ship = self.ships[ship_name]
            print("ship: {}".format(ship))

            to = random.choice(self.field)
            # print("to: {}", to) #to = [2, 1]
            while not ship.can_reach(to) or not self.overlap(to) is None:
                to = random.choice(self.field)

            return json.dumps(self.move(ship.type, to))
        elif act == "attack":
            to = random.choice(self.field)
            while not self.can_attack(to):
                to = random.choice(self.field)

            return json.dumps(self.attack(to))



# 仕様に従ってサーバとソケット通信を行う．
def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            print(get_msg)
            player = Player_2(seed)
            sockfile.write(player.initial_condition()+'\n')
            past_msg = ""

            while True:
                info = sockfile.readline().rstrip() #rstrip: 文字列の右側から「除去する文字」に該当する文字が削除されます。指定がない場合はスペースが削除される。
                print(info)
                if info == "your turn": #攻撃か移動かを選ぶ
                    
                    # print("past_msg: ", type(past_msg), past_msg) #前に相手が攻撃or移動をしていれば、それに伴う結果が残っている

                    sockfile.write(player.action(past_msg)+'\n') #actionにpast_msgを渡して、その結果によって次の行動選択を行う。
                    get_msg = sockfile.readline()

                    # print("your turn get_msg: ", get_msg)
                    """
                    get_msg: 自分の行動による結果
                    {
                        "result":{"attacked":{"position":[2,1],"near":["c"]}}, #最初は攻撃も移動もしていないため、取得されるのはconditionのみ
                        "condition":{
                            "me":
                                {"w":{"hp":3,"position":[2,2]},"c":{"hp":2,"position":[1,4]},"s":{"hp":1,"position":[2,3]}},
                            "enemy":
                                {"w":{"hp":3},"c":{"hp":2},"s":{"hp":1}}}
                    }
                    """

                    player.update(get_msg)
                elif info == "waiting": #相手の行動選択待ち
                    get_msg = sockfile.readline()

                    # print("waiting get_msg: ", get_msg)
                    """
                    get_msg: 相手の行動による結果
                    {
                        "result":{"moved":{"ship":"w","distance":[0,2]}}, #相手の移動情報、">>"と同じ
                        "condition":{
                            "me":{"w":{"hp":3,"position":[2,2]},"c":{"hp":2,"position":[1,4]},"s":{"hp":1,"position":[2,3]}},
                            "enemy":{"w":{"hp":3},"c":{"hp":2},"s":{"hp":1}}}
                    }
                    """
                    player.update(get_msg)
                    past_msg = get_msg #相手の行動による結果を記憶しておく
                elif info == "you win":
                    break
                elif info == "you lose":
                    break
                elif info == "even":
                    break
                else:
                    raise RuntimeError("unknown information")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sample Player for Submaline Game")
    parser.add_argument(
        "host",
        metavar="H",
        type=str,
        help="Hostname of the server. E.g., localhost",
    )
    parser.add_argument(
        "port",
        metavar="P",
        type=int,
        help="Port of the server. E.g., 2000",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed of the player",
        required=False,
        default=0,
    )
    args = parser.parse_args()

    main(args.host, args.port, seed=args.seed)
