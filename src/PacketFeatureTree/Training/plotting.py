from matplotlib.patches import Rectangle

def add_patches(ax, pred, cs, lengths_dict, c='r', f='none', a=1, linestyle = 'solid'):
    s = -0.45
    for i, p in enumerate(pred):
        l = lengths_dict[p]
        if i==0: #or i==len(pred)-1:
            l -= 0.05
        if i == len(pred)-1:
            l += 0.05
        
        ax.add_patch(Rectangle((s, list(cs).index(p) - 0.475), l, 0.95, linewidth=2, edgecolor=c, facecolor=f, alpha=a, linestyle = linestyle))
        if i==0:
            s-=0.1
            #i=9
        s+= lengths_dict[p]