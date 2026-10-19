"""Entrenamiento con acumulación de gradientes y ponderación por imagen."""
from itertools import islice


def entrenar_epoca(model, loader, device, optimizer, preparar_target, clip_gradiente,
                   acumulacion=1, max_grad_norm=0):
    """Una actualización por grupo, incluida la cola de tamaño incompleto.

    Pondera cada pérdida media por las imágenes de su microbatch. Conserva el
    lote efectivo sin retener varios grafos a la vez; no promete identidad
    numérica con un forward grande (muestreo de propuestas y redondeos cambian).
    """
    if acumulacion < 1:
        raise ValueError('acumulacion debe ser al menos 1')
    iterator=iter(loader)
    losses=[]
    model.train()
    while True:
        grupo=list(islice(iterator, acumulacion))
        if not grupo:
            break
        n=sum(len(images) for images,_ in grupo)
        if not n:
            raise ValueError('El grupo no contiene imágenes')
        optimizer.zero_grad()
        for images, targets in grupo:
            images=[image.to(device) for image in images]
            targets=[preparar_target(target, device) for target in targets]
            loss=sum(model(images, targets).values())
            (loss * (len(images)/n)).backward()
            losses.append(loss.item())
        clip_gradiente(optimizer.param_groups, max_norm=max_grad_norm)
        optimizer.step()
    return losses
