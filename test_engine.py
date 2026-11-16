import unittest
from game import Game
from enemy import path
from settings import SIZE

class RulesTests(unittest.TestCase):
    def plain(self):
        g=Game(seed=7)
        g.walls=set(); g.sources=set(); g.player=(14,0); g.enemy=(0,0)
        return g

    def test_generated_maps(self):
        for difficulty, count in [('easy',5),('normal',8),('hard',10)]:
            for seed in range(200):
                g=Game(difficulty,seed)
                self.assertEqual(len(g.sources),count)
                self.assertFalse(g.walls & g.sources)
                self.assertTrue(path(g.player,g.exit,g.walls | g.sources))
                self.assertTrue(path(g.enemy,g.player,g.walls))
                self.assertNotIn(g.player,g.sources)
                self.assertNotIn(g.exit,g.sources)

    def test_count_center_and_edges(self):
        g=self.plain(); g.sources={(0,0),(0,1),(1,1),(14,14)}
        self.assertEqual(g.count((0,0),False),2)
        self.assertEqual(g.count((0,0),True),3)
        self.assertEqual(g.count((14,14),False),0)
        self.assertEqual(g.count((14,14),True),1)

    def test_invalid_move_does_not_consume_turn(self):
        g=self.plain(); g.walls={(13,0)}; enemy=g.enemy
        self.assertFalse(g.move(-1,0)); self.assertFalse(g.move(1,0))
        self.assertFalse(g.move(1,1))
        self.assertEqual(g.turn,0); self.assertEqual(g.enemy,enemy)

    def test_scan_consumes_exactly_one_turn(self):
        g=self.plain(); p=g.player
        self.assertFalse(g.scan([(14,0),(14,0)]))
        self.assertFalse(g.scan([(14,0),(0,0)]))
        self.assertEqual(g.turn,0)
        self.assertTrue(g.scan([(14,0),(13,1)]))
        self.assertEqual(g.turn,1); self.assertEqual(g.player,p)
        self.assertEqual(len(g.scans),2); self.assertEqual(g.enemy,(1,0))
        self.assertEqual(g.next_enemy_mode,'랜덤 이동')

    def test_bfs_avoids_walls(self):
        route=path((0,0),(0,2),{(0,1)})
        self.assertEqual(len(route),5)
        self.assertNotIn((0,1),route)
        self.assertFalse(path((0,0),(0,2),{(0,1),(1,0)}))

    def test_win_before_enemy_action(self):
        g=self.plain(); g.player=(0,13); g.enemy=(1,14)
        self.assertTrue(g.move(0,1))
        self.assertEqual(g.status,'won'); self.assertEqual(g.enemy,(1,14))
        self.assertFalse(g.move(0,-1))

    def test_source_death(self):
        g=self.plain(); g.sources={(13,0)}
        g.move(-1,0); self.assertEqual(g.status,'lost'); self.assertEqual(g.enemy,(0,0))

    def test_enemy_contact_both_directions(self):
        g=self.plain(); g.enemy=(13,0)
        g.move(-1,0); self.assertEqual(g.status,'lost')
        g=self.plain(); g.enemy=(12,0)
        g.move(-1,0); self.assertEqual(g.status,'lost'); self.assertEqual(g.enemy,g.player)

    def test_random_step_is_legal(self):
        g=self.plain(); g.walls={(0,1)}; g.turn=2
        before=g.enemy; g.enemy_step()
        self.assertEqual(abs(g.enemy[0]-before[0])+abs(g.enemy[1]-before[1]),1)
        self.assertNotIn(g.enemy,g.walls)

    def test_seed_reproducibility(self):
        a=Game(seed=42); b=Game(seed=42)
        self.assertEqual(a.walls,b.walls); self.assertEqual(a.sources,b.sources)
        for _ in range(4):
            a.scan([(14,0),(14,1)]); b.scan([(14,0),(14,1)])
            self.assertEqual(a.enemy,b.enemy)

if __name__=='__main__': unittest.main()
