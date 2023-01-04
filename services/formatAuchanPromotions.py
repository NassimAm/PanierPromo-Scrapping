def formatAuchanPromotions(data):
    fData = []
    for dt in data:
        id = dt[2]
        prix = dt[1]
        promos = dt[0]
        for promo in promos.split(' | '):
            type = 'n/a'
            numProduit = "1"
            reduction = "0"
            if (len(promo) > 0):
                if("%" in promo):
                    if ("-" in promo):
                        type = "reduction"
                        if("sur" in promo):
                            numProduit = promo.split()[3][0]
                        reduction = promo.split()[0][1:-1]
                    elif ("cagnotté" in promo):
                        type = "économisé"
                        if("sur" in promo):
                            numProduit = promo.split()[4][0]
                        reduction = promo.split()[0][:-1]
                elif("€" in promo):
                    type = "iRemise"
                    if("-" in promo):
                        reduction = promo[1:-1]
                    elif("si"):
                        numProduit = promo.split()[4]
                        reduction = promo.split()[0][:-1]
                elif("=" in promo):
                    type = "combinaison"
                    numProduit = promo.split()[0]
                    reduction = str((int(numProduit) - int(promo.split()[3]))*100)
                elif("Offre spéciale" in promo):
                    type = "catalogue"
            elif(len(promo) == 0):
                type = "catalogue"

            for codebar in id.split('/')[1:]:
                fData.append([codebar.replace(' ',''), prix, type, numProduit, reduction])
    return fData