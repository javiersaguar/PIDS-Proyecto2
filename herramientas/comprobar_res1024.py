"""Prueba dos microbatches y una inferencia sin guardar pesos ni iniciar otra ejecución."""
import json
from pathlib import Path
import sys

repo=Path(__file__).resolve().parents[1]
nb=repo/'ENTREGA 1/WEEK2/train_res1024.ipynb'
n=json.loads(nb.read_text(encoding='utf-8'))
scope={}
for i in (2,4,6,8,10,11,12,13):
    exec(compile(''.join(n['cells'][i]['source']),f'preflight_cell_{i}','exec'),scope)
torch=scope['torch']
assert torch.cuda.is_available(), 'No hay GPU disponible'
assert not Path(scope['model_best_path']).exists() and not Path(scope['model_last_path']).exists(), 'Ya hay pesos en el destino'
dataset=scope['CustomDataset'](scope['path_data_train'], transform=scope['get_transform'](),incluir_aumentadas=True)
assert len(dataset)==3184
loader=scope['DataLoader'](dataset,batch_size=scope['batch_size'],shuffle=False,collate_fn=scope['collate_fn'])
model,opt,history,device=scope['get_model'](scope['model_name'],num_classes=2,
    lr_data=[scope['lr'],scope['lr_momentum'],scope['lr_decay']],pretrained=True,use_gpu=True)
assert model.transform.min_size==(1024,) and model.transform.max_size==1820
torch.cuda.reset_peak_memory_stats()
it=iter(loader);batches=[next(it),next(it)]
losses=scope['entrenar_epoca'](model,batches,device,opt,scope['sin_difficult'],scope['clip_grad_norms'],acumulacion=2)
assert all(__import__('math').isfinite(x) for x in losses), losses
model.eval()
with torch.no_grad():
    outputs=model([im.to(device) for im in batches[0][0]])
torch.cuda.synchronize()
result=dict(estado='ok',experimento=scope['experimento'],microbatch=scope['batch_size'],
            acumulacion=2,batch_efectivo=8,min_size=list(model.transform.min_size),max_size=model.transform.max_size,
            perdidas=losses,memoria_max_reservada_mib=round(torch.cuda.max_memory_reserved()/1024**2,1),
            memoria_total_mib=round(torch.cuda.get_device_properties(0).total_memory/1024**2,1),
            detecciones=[len(x['boxes']) for x in outputs],checkpoint_guardado=False)
path=nb.parent/'preflight_res1024.json'
path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
