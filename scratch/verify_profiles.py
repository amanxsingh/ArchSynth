profiles = [
    ('online_async_launch.py', 22, 8, 2, 1, 2, 2, 1, 9, 1),
    ('online_sync_launch.py', 23, 8, 2, 1, 2, 2, 1, 10, 1),
    ('localization_launch.py', 22, 8, 2, 1, 2, 2, 1, 9, 1),
    ('lifelong_launch.py', 22, 8, 2, 1, 2, 2, 1, 9, 1),
    ('offline_launch.py', 23, 8, 2, 1, 2, 2, 1, 10, 1),
    ('online_async_decentralized_multirobot_launch.py', 24, 9, 2, 1, 3, 2, 1, 9, 1),
    ('merge_maps_kinematic_launch.py [N=1]', 7, 4, 1, 1, 0, 0, 1, 2, 1),
]

print(f"{'Profile':<50} | {'App':<4} | {'Pubs':<4} | {'Subs':<4} | {'Srvs':<4} | {'Entities':<8} | {'Writers':<7} | {'Readers':<7} | {'Endpoints':<9}")
print('-' * 115)

tot_app = tot_pubs = tot_subs = tot_srvs = tot_ent = tot_w = tot_r = tot_ep = 0
for name, app, d_pub, tf_b, ims_pub, d_sub, tf_l_sub, ims_sub, app_srv, ims_srv in profiles:
    pubs = d_pub + tf_b + ims_pub
    subs = d_sub + tf_l_sub + ims_sub
    srvs = app_srv + ims_srv
    ent = pubs + subs + srvs
    writers = pubs + srvs
    readers = subs + srvs
    ep = writers + readers
    print(f"{name:<50} | {app:<4} | {pubs:<4} | {subs:<4} | {srvs:<4} | {ent:<8} | {writers:<7} | {readers:<7} | {ep:<9}")
    tot_app += app
    tot_pubs += pubs
    tot_subs += subs
    tot_srvs += srvs
    tot_ent += ent
    tot_w += writers
    tot_r += readers
    tot_ep += ep

print('-' * 115)
print(f"{'TOTAL AGGREGATE [N=1]':<50} | {tot_app:<4} | {tot_pubs:<4} | {tot_subs:<4} | {tot_srvs:<4} | {tot_ent:<8} | {tot_w:<7} | {tot_r:<7} | {tot_ep:<9}")
