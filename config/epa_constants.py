# EPA 等級對應表
EPA_LEVEL_MAPPING = {
    # 整合重複的尺規格式
    '不允許學員觀察': 1,
    '學員在旁觀察': 1.5,
    '允許學員在旁觀察': 1.5,
    '教師在旁逐步共同操作': 2,
    '教師在旁必要時協助': 2.5,
    '教師可立即到場協助，事後逐項確認': 3,
    '教師可立即到場協助，事後重點確認': 3.3,
    '教師可稍後到場協助，必要時事後確認': 3.6,
    '教師on call提供監督': 4,
    '教師不需on call，事後提供回饋及監督': 4.5,
    '學員可對其他資淺的學員進行監督與教學': 5,
    
    # 整合其他支援文字格式
    '教師在旁逐步共同操作': 2,
    '教師在旁必要時協助 ': 2.5,
    '教師可立即到場協助，事後須再確認': 3,
    '教師可稍後到場協助，重點須再確認': 4,
    '我可獨立執行': 5,
    
    # 整合重複的 Level 格式
    'Level I': 1, ' Level I': 1, 'Level1': 1, 'Level 1': 1,
    'Level 1&2': 1.5, 'Level1&2': 1.5, 'LevelI&2': 1.5, 'Level&2': 1.5,
    'Level II': 2, ' Level II': 2, 'Level2': 2, 'Level 2': 2,
    'Level2&3': 2.5, 'Level 2&3': 2.5, 'Leve 2&3': 2.5,
    'Level 2a': 2, 'Level2a': 2, 'Level 2b': 2.5, 'Level2b': 2.5,
    'Level III': 3, ' Level III': 3, 'Level3': 3, 'Level 3': 3,
    'Level 3a': 3, 'Level3a': 3, 'Level 3b': 3.3, 'Level3b': 3.3,
    'Level3c': 3.6, 'Level 3c': 3.6,
    'Level 3&4': 3.5, 'Level3&4': 3.5, 'Leve 3&4': 3.5, 'Lvel 3&4': 3.5,
    'Level IV': 4, ' Level IV': 4, 'Level4': 4, 'Level 4': 4,
    'Level4&5': 4.5, 'Level 4&5': 4.5,
    'Level 5': 5, 'Level V': 5, ' Level V': 5, 'Level5': 5
} 