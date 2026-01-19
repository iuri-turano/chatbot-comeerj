import torch
import subprocess
import sys

print("=" * 70)
print("🔍 DIAGNÓSTICO DE GPU - Assistente Espírita")
print("=" * 70)

# 1. Verificar PyTorch e CUDA
print("\n1️⃣ PYTORCH E CUDA")
print(f"   PyTorch versão: {torch.__version__}")
print(f"   CUDA disponível: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"   ✅ CUDA detectado!")
    print(f"   CUDA versão: {torch.version.cuda}")
    print(f"   Número de GPUs: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        print(f"\n   GPU {i}:")
        print(f"   - Nome: {torch.cuda.get_device_name(i)}")
        props = torch.cuda.get_device_properties(i)
        print(f"   - VRAM Total: {props.total_memory / 1024**3:.2f} GB")
        print(f"   - VRAM Usada: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
        print(f"   - VRAM Livre: {(props.total_memory - torch.cuda.memory_allocated(i)) / 1024**3:.2f} GB")
else:
    print("   ❌ CUDA NÃO disponível")
    print("\n   Possíveis causas:")
    print("   1. PyTorch instalado sem suporte CUDA")
    print("   2. Driver NVIDIA não instalado")
    print("   3. CUDA Toolkit não instalado")
    print("   4. Versão incompatível")

# 2. Verificar NVIDIA Driver
print("\n2️⃣ NVIDIA DRIVER")
try:
    result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print("   ✅ NVIDIA Driver instalado")
        # Extrair versão do driver
        lines = result.stdout.split('\n')
        for line in lines:
            if 'Driver Version' in line:
                print(f"   {line.strip()}")
                break
    else:
        print("   ❌ nvidia-smi falhou")
except FileNotFoundError:
    print("   ❌ nvidia-smi não encontrado")
    print("   Driver NVIDIA não está instalado ou não está no PATH")
except Exception as e:
    print(f"   ❌ Erro ao verificar: {e}")

# 3. Verificar instalação do PyTorch
print("\n3️⃣ INSTALAÇÃO DO PYTORCH")
try:
    # Verificar se foi instalado com CUDA
    if '+cu' in torch.__version__:
        cuda_version = torch.__version__.split('+cu')[1]
        print(f"   ✅ PyTorch instalado com CUDA {cuda_version}")
    else:
        print("   ⚠️ PyTorch instalado SEM suporte CUDA")
        print("   Versão CPU detectada")
except:
    print("   ⚠️ Não foi possível determinar tipo de instalação")

# 4. Teste simples de GPU
print("\n4️⃣ TESTE DE GPU")
if torch.cuda.is_available():
    try:
        # Criar tensor na GPU
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = x @ y
        print("   ✅ Operação na GPU bem-sucedida!")
        print(f"   Device usado: {z.device}")
    except Exception as e:
        print(f"   ❌ Erro ao usar GPU: {e}")
else:
    print("   ⏭️ Pulado (CUDA não disponível)")

# 5. Recomendações
print("\n5️⃣ RECOMENDAÇÕES")
print("=" * 70)

if not torch.cuda.is_available():
    print("\n⚠️ CUDA NÃO ESTÁ DISPONÍVEL")
    print("\nPara corrigir:")
    print("\n1. Verifique se você tem GPU NVIDIA:")
    print("   - Abra 'Gerenciador de Dispositivos'")
    print("   - Procure por 'Adaptadores de vídeo'")
    print("   - Deve aparecer algo como 'NVIDIA GeForce...'")
    
    print("\n2. Instale o Driver NVIDIA:")
    print("   - https://www.nvidia.com/Download/index.aspx")
    print("   - Ou use GeForce Experience")
    
    print("\n3. Reinstale PyTorch COM suporte CUDA:")
    print("   ")
    print("   # Desinstalar versão atual")
    print("   pip uninstall torch torchvision torchaudio")
    print("   ")
    print("   # Instalar com CUDA 11.8 (recomendado)")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print("   ")
    print("   # OU CUDA 12.1")
    print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    
    print("\n4. Reinicie o terminal/IDE depois de instalar")

else:
    print("\n✅ GPU ESTÁ FUNCIONANDO!")
    print("\nSeu sistema está configurado corretamente.")
    
    # Informações adicionais
    props = torch.cuda.get_device_properties(0)
    vram_total = props.total_memory / 1024**3
    
    print(f"\n📊 Capacidade estimada:")
    print(f"   VRAM disponível: {vram_total:.1f} GB")
    
    if vram_total >= 8:
        print("   ✅ Suficiente para ambos os modelos (llama3.2:3b + qwen2.5:7b)")
    elif vram_total >= 6:
        print("   ⚠️ Limite para modelos grandes. Considere usar modelos menores.")
    else:
        print("   ❌ VRAM insuficiente. Use modelos de 1B-3B apenas.")

print("\n" + "=" * 70)
print("🏁 DIAGNÓSTICO COMPLETO")
print("=" * 70)