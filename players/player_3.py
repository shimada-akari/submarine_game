"""
attackがhitまたはnearした場合は、それに合わせて次の行動を選択する。
attackがhitまたはnearしなかった場合は、player_1と同様の選択をする。
"""


import json
import os
import random
import socket
import sys

sys.path.append(os.getcwd())

from lib.player_base import Player, PlayerShip

def get_hit_in_pre_enemy_attack(past_attacked, my_ships):
    """
    敵にattackされ、hitされた時の次の自分の行動を考える
    """
    if past_attacked["hit"] in my_ships: #hitされた船が残っている
        #past_attacked["hit"] : hitされた船の名前( "s" )が返ってくる
        #hitされた船を移動させる。（第一優先）
        print("attacked hit.")
        act = "move"
        ship_name = past_attacked["hit"]
        
    else: #hitで船が無くなった
        if past_attacked["near"] != []: #hitで船が無くなった かつ nearで位置がバレそうな船がある。
            act = "move"
            ship_name = random.choice(past_attacked["near"])#とりあえず、ランダムで船を選んで移動させる。

        else:
            print("lost ship by hit.")
            act = "attack"
            ship_name = None #次に取る行動は攻撃なので、ship_nameは関係ない

    return act, ship_name


def get_near_ship(past_attack):
    return past_attack["near"]


def action_when_pre_action_does_not_hit_or_near(ene_past_result, ene_past_condition):
    """
    ・1つ前の自分の攻撃がhitもnearもなかった場合
    ・nearはあったが、敵がmoveしたためnear shipの場所推定が不可能な場合
    ・自分初手、後攻の場合
    1つ前の相手の攻撃に基づいて、次の自分の攻撃を決める。
    返り値：act, ship_name(act=="attack"の時はship_name=Noneとする。)
    """
    if "attacked" in ene_past_result: #attackされた
        ene_past_attack = ene_past_result["attacked"]
        #moveを選択するとき：hitかつhitされた船が残っている または nearがある

        # print("past_attacked[near] != []", past_attacked["near"] != [])
        my_near_ships = get_near_ship(ene_past_attack) #敵からの攻撃により、near shipとなった船の名前を取得

        if "hit" in ene_past_attack: #hitされた
            my_ships = ene_past_condition["me"]
            act, ship_name = get_hit_in_pre_enemy_attack(ene_past_attack, my_ships)

        elif my_near_ships != []: #hitされた船はないが、nearで位置がバレそうな船がある。
            #nearであげられた船の1つを移動させる。（第二優先）<-nearで複数の船があげられたとき、どの船を優先的に動かすべきか？？ 
            #一番移動回数が少ないものを動かした方が良いのでは？　動かす回数が多いと履歴で場所が分かりそう。
            print("attacked near.")
            act = "move"
            ship_name = random.choice(my_near_ships)#とりあえず、ランダムで船を選んで移動させる。
        
        else: #attackedでhit/nearがなかった
            print("attacked but safe.")
            act = "attack"
            ship_name = None

    else: #相手の行動がmovedのとき
        print("moved.")
        act = "attack"
        ship_name = None

    return act, ship_name


def find_not_moved_enemys_near_ship(near_ships, past_result):
    print("near_ships: ", near_ships)
    print("past_result: ", past_result)

    if "moved" in past_result:
        moved_ship = past_result["moved"]["ship"]
        if moved_ship in near_ships:
            not_moved_ships = near_ships.copy()
            # print("copy_near_ships: ", near_ships_copy)
            not_moved_ships.remove(moved_ship)
            # print("id not_moved_ships: ", not_moved_ships)
        else:
            not_moved_ships = near_ships
    else:
        not_moved_ships = near_ships
    # print("not_moved_ships: ", not_moved_ships)
    return not_moved_ships
            

def get_attack_position(past_attack):
    return past_attack["position"]

def decide_attack_position_from_8_periferal(past_attack):
    position = get_attack_position(past_attack)
    x_add = random.choice([-1, 0, 1])
    y_add = random.choice([-1, 0, 1])
    
    while 
    x_add == 0 and y_add == 0: #positionと同じ場所をnew_positionとしないようにする
        x_add = random.choice([-1, 0, 1])
        y_add = random.choice([-1, 0, 1])


    new_position = [position[0] + x_add, position[1] + y_add ]
    return new_position


def considering_near_ship(my_past_attack, ene_past_result, ene_past_condition):
    ene_near_ships = get_near_ship(my_past_attack) #敵のnear ship informationを取得する
    if len(ene_near_ships) != 0:
        not_moved_ships = find_not_moved_enemys_near_ship(ene_near_ships, ene_past_result) #nearの船のうちmoveしていないship nameをリストで返す
        if len(not_moved_ships) != 0: #1つでも移動していない船があれば、attackしたpositionの8近傍をattackする
            attack_position = decide_attack_position_from_8_periferal(my_past_attack) #8近傍からランダムに1つを選び、attack positionとする
            act = "attack"
            ship_name = None
        else:
            act, ship_name = action_when_pre_action_does_not_hit_or_near(ene_past_result, ene_past_condition) #nearはあったが、移動しているため場所推定が不可能。
            attack_position = None

    else: #hitしたが沈没済み、nearもなかった
        act, ship_name = action_when_pre_action_does_not_hit_or_near(ene_past_result, ene_past_condition)
        attack_position = None
    return act, attack_position, ship_name



def check_enemys_hit_ship_situation(hit_ship, attack_condition):
    enemy_ships = attack_condition["enemy"] #{'w': {'hp': 3}, 's': {'hp': 1}} 敵の存在している船
    if hit_ship in enemy_ships: #hitした船はまだ存在している
        return True
    else: #hitした船は沈没した
        return False

def cal_current_position(ship_name, pre_position, past_result):
    """
    ship_name: 現在地を計算する対象の船の名前
    movedをする前の ship_name の居場所
    past_result: movedをした時のresult (実際にmovedした船が ship_nameと一致していなくても可)
    """
    moved_info = past_result["moved"] #{"ship":"w","distance":[0,1]}
    moved_ship = moved_info["ship"] #実際にmovedした船の名前
    if moved_ship == ship_name:
        distance = moved_info["distance"]
        new_position = [pre_position[0] + distance[0], pre_position[1] + distance[1]]
        
    else: #実際にmovedした船 != ship_name　→ ship_nameの現在地はpre_positionのまま
        new_position = pre_position
    return new_position




def search_enemys_hit_ship_position(hit_ship, hit_position, ene_past_result):
    if "moved" in ene_past_result: #hitした船、または別の船が移動したので、hitした船の現在地を計算する
        new_position = cal_current_position(hit_ship, hit_position, ene_past_result)
    else: #hitした船は同じ場所にいる
        new_position = hit_position
    return new_position




def action_when_pre_action_hit_or_near(my_past_result, my_past_condition, ene_past_result, ene_past_condition):
    my_past_attack = my_past_result["attacked"]
    
    if "hit" in my_past_attack: #hitした
        hit_ship = my_past_attack["hit"]
        hit_position = my_past_attack["position"]
        ene_ship_situation = check_enemys_hit_ship_situation(hit_ship, my_past_condition) #hitした敵の船が存在するかをture/falseで返す
        if ene_ship_situation: #存在する
            attack_position = search_enemys_hit_ship_position(hit_ship, hit_position, ene_past_result) #hitした敵の船の場所を計算する
            act = "attack"
            ship_name = None

        else: #hitした敵の船は沈没した→near shipの情報から次の行動を決める
            act, attack_position, ship_name = considering_near_ship(my_past_attack, ene_past_result, ene_past_condition)

    else: #hitなし→near shipの情報から次の行動を決める
        act, attack_position, ship_name = considering_near_ship(my_past_attack, ene_past_result, ene_past_condition)

    return act, attack_position, ship_name



def action_considering_2pre_actions(my_past_result, my_past_condition, ene_past_result, ene_past_condition):
    if "attacked" in my_past_result:
        act, attack_position, ship_name = action_when_pre_action_hit_or_near(my_past_result, my_past_condition, ene_past_result, ene_past_condition)

    else: #1つ前の自分の行動がmoveだった場合
        act, ship_name = action_when_pre_action_does_not_hit_or_near(ene_past_result, ene_past_condition)
        attack_position = None

    return act, attack_position, ship_name


def get_dic_from_json(json_info):
    past_info = eval(json_info)
    past_result = past_info["result"]
    past_condition = past_info["condition"]  
    return past_result, past_condition 



class Player_1(Player):

    def __init__(self, seed=0):
        random.seed(seed)

        # フィールドを2x2の配列として持っている．
        self.field = [[i, j] for i in range(Player.FIELD_SIZE)
                      for j in range(Player.FIELD_SIZE)]

        # 初期配置を非復元抽出でランダムに決める．
        ps = random.sample(self.field, 3)
        positions = {'w': ps[0], 'c': ps[1], 's': ps[2]}
        super().__init__(positions)


    def action_move(self, ship_name):
        # ship = random.choice(list(self.ships.values()))
        ship = self.ships[ship_name]
        print("ship: {}".format(ship))

        to = random.choice(self.field) #どのくらい移動するのかはランダムで決める
        while not ship.can_reach(to) or not self.overlap(to) is None:
            to = random.choice(self.field)

        return ship, to

    def action_attack(self, attack_position):
        if attack_position:
            to = attack_position
            # print("attack_position to: ", type(to), to)
        else:
            to = random.choice(self.field)
            while not self.can_attack(to):
                to = random.choice(self.field)
                # print("random choice to: ", type(to), to)
        return to


    def action(self, past_results):
        attack_position = None
        ship_name = None

        if len(past_results) == 0: #len == 0 自分初手、先行
            # print("result not fount.")
            act = "attack" 

        elif len(past_results) == 1: #自分初手、後攻
            ene_past_info = past_results[0]
            get_dic_from_json(ene_past_info)
            ene_past_result, ene_past_condition = ene_past_info = eval(ene_past_info)
            act, ship_name = action_when_pre_action_does_not_hit_or_near(ene_past_result, ene_past_condition)
            attack_position = None
        
        else:
            my_past_info = past_results[0]
            ene_past_info = past_results[1]

            my_past_result, my_past_condition = get_dic_from_json(my_past_info)
            ene_past_result, ene_past_condition = get_dic_from_json(ene_past_info)
            
            act, attack_position, ship_name = action_considering_2pre_actions(my_past_result, my_past_condition, ene_past_result, ene_past_condition)

        if act == "attack":
            assert(ship_name == None)
        else:
            assert(attack_position == None)

        print("choice : ", act, end="   ")

        if act == "move":
            ship, move_to = self.action_move(ship_name)
            print("ship : {}   move_to : {}".format(ship, move_to))
            return json.dumps(self.move(ship.type, move_to))

        elif act == "attack":
            attack_to = self.action_attack(attack_position)
            print("attack_to : {}".format(attack_to))
            return json.dumps(self.attack(attack_to))



# 仕様に従ってサーバとソケット通信を行う．
def main(host, port, seed=0):
    assert isinstance(host, str) and isinstance(port, int)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        with sock.makefile(mode='rw', buffering=1) as sockfile:
            get_msg = sockfile.readline()
            # print("player3 get_msg: ", get_msg)
            player = Player_1(seed)
            sockfile.write(player.initial_condition()+'\n')
            past_msgs = []

            while True:
                info = sockfile.readline().rstrip() #rstrip: 文字列の右側から「除去する文字」に該当する文字が削除されます。指定がない場合はスペースが削除される。
                print(info)
                if info == "your turn": #攻撃か移動かを選ぶ
                
                    sockfile.write(player.action(past_msgs)+'\n') #actionにpast_msgを渡して、その結果によって次の行動選択を行う。
                    get_msg = sockfile.readline()

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
                    print("player_3 your turn get_msg: ", get_msg)
                    player.update(get_msg)
                    past_msgs = [get_msg] #常に自分の行動結果がpast_msgsのindex0に入るようにする。次の行動を取る時(ここから2回目のループの時、はindex0に1つ前の自分の行動結果、index1に1つ前の相手の行動結果が入っている。)


                elif info == "waiting": #相手の行動選択待ち
                    get_msg = sockfile.readline()
                    """
                    get_msg: 相手の行動による結果
                    {
                        "result":{"moved":{"ship":"w","distance":[0,2]}}, #相手の移動情報、">>"と同じ
                        "condition":{
                            "me":{"w":{"hp":3,"position":[2,2]},"c":{"hp":2,"position":[1,4]},"s":{"hp":1,"position":[2,3]}},
                            "enemy":{"w":{"hp":3},"c":{"hp":2},"s":{"hp":1}}}
                    }
                    """
                    print("player_3 waiting get_msg: ", get_msg)
                    player.update(get_msg)

                    if len(past_msgs) != 0: #自分先行の場合、past_msgsには既に自分のresultが入っている
                        past_msgs.append(get_msg)

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
