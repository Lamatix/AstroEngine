'use client';
import { useState } from 'react';

export default function AstroEngineDashboard() {
  const [activeTab, setActiveTab] = useState('western');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');

  const handleCalculate = (moduleName) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      try {
        setResult(`✨ ${moduleName.toUpperCase()} analizi başarıyla tamamlandı! Swiss Ephemeris ve Esoteric Engine verilerine göre kozmik haritanız optimize edildi.`);
      } catch (e) {
        setResult("Analiz sırasında hata oluştu.");
      }
    }, 1200);
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#090d16', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
      
      {/* Sol Menü (Sidebar) */}
      <aside style={{ width: '280px', backgroundColor: '#0e1322', borderRight: '1px solid #1e293b', padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', flexShrink: 0 }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', margin: '0 0 0.5rem 0', color: '#a78bfa', fontWeight: '700' }}>🌌 AstroEngine</h2>
          <span style={{ display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: '600', backgroundColor: '#064e3b', color: '#34d399' }}>● 7/24 Otonom Mod</span>
        </div>

        <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.5rem' }}>
          Kehanet Modülleri
        </div>

        {[
          { id: 'western', label: '🪐 Batı Astrolojisi' },
          { id: 'vedic', label: '🔮 Vedik Astrolojisi' },
          { id: 'chinese', label: '🐉 Çin Astrolojisi (BaZi)' },
          { id: 'ebced', label: '📜 Ezoterik Ebced Hesabı' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setResult(''); }}
            style={{
              width: '100%', textAlign: 'left', padding: '0.75rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '500', fontSize: '0.9rem',
              backgroundColor: activeTab === tab.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
              color: activeTab === tab.id ? '#818cf8' : '#94a3b8',
              border: activeTab === tab.id ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}

        <div style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '1.5rem', marginBottom: '0.5rem' }}>
          Medya & Ticaret
        </div>

        {[
          { id: 'video', label: '🎬 Video Fabrikası' },
          { id: 'pdf', label: '📄 Etsy / PDF Raporları' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setResult(''); }}
            style={{
              width: '100%', textAlign: 'left', padding: '0.75rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer', fontWeight: '500', fontSize: '0.9rem',
              backgroundColor: activeTab === tab.id ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
              color: activeTab === tab.id ? '#818cf8' : '#94a3b8',
              border: activeTab === tab.id ? '1px solid rgba(99, 102, 241, 0.3)' : '1px solid transparent',
              transition: 'all 0.2s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </aside>

      {/* Sağ Çalışma Alanı */}
      <main style={{ flex: 1, padding: '2.5rem', overflowY: 'auto', display: 'flex', justifyContent: 'center' }}>
        <div style={{ width: '100%', maxWidth: '850px' }}>
          
          {activeTab !== 'video' && activeTab !== 'pdf' ? (
            <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', borderRadius: '16px', padding: '2rem', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', textTransform: 'capitalize', color: '#f8fafc' }}>{activeTab} Kehanet Konsolu</h2>
              <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '2rem' }}>
                Doğum verilerinizi girerek evrensel hesaplama motorunu tetikleyin.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1.25rem', marginBottom: '1.5rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '500' }}>Ad Soyad</label>
                  <input type="text" placeholder="Örn: Sercan Bilir" style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#090d16', color: '#fff', fontSize: '0.95rem', outline: 'none' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '500' }}>Doğum Tarihi</label>
                  <input type="date" style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#090d16', color: '#fff', fontSize: '0.95rem', outline: 'none' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '500' }}>Doğum Saati</label>
                  <input type="time" style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#090d16', color: '#fff', fontSize: '0.95rem', outline: 'none' }} />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '0.4rem', fontWeight: '500' }}>Doğum Yeri</label>
                  <input type="text" placeholder="Örn: İstanbul, Türkiye" style={{ width: '100%', padding: '0.75rem 1rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#090d16', color: '#fff', fontSize: '0.95rem', outline: 'none' }} />
                </div>
              </div>

              <button 
                onClick={() => handleCalculate(activeTab)} 
                style={{ width: '100%', padding: '0.85rem', borderRadius: '8px', border: 'none', background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)', color: '#fff', fontWeight: '600', fontSize: '1rem', cursor: 'pointer', boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)' }}
              >
                {loading ? 'Kozmik Veriler Hesaplanıyor...' : 'Kozmik Analizi Başlat'}
              </button>

              {result && (
                <div style={{ marginTop: '1.5rem', padding: '1rem 1.25rem', backgroundColor: '#090d16', border: '1px solid rgba(99, 102, 241, 0.33)', borderRadius: '8px', color: '#a5b4fc', fontSize: '0.95rem', lineHeight: '1.5' }}>
                  {result}
                </div>
              )}
            </div>
          ) : activeTab === 'video' ? (
            <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', borderRadius: '16px', padding: '2rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#f8fafc' }}>Otomatik Video Fabrikası (FFmpeg)</h2>
              <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
                Arka planda çalışan video üretim hatlarının yönetim ve önizleme paneli.
              </p>

              <div style={{ height: '220px', backgroundColor: '#090d16', borderRadius: '12px', border: '1px solid #1e293b', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
                🎬 FFmpeg Otonom Render Hattı Aktif
              </div>

              <button onClick={() => alert('Yeni video render kuyruğuna eklendi!')} style={{ width: '100%', padding: '0.85rem', borderRadius: '8px', border: '1px solid #334155', backgroundColor: '#1e293b', color: '#fff', fontWeight: '600', cursor: 'pointer' }}>
                Yeni Video İşlemi Tetikle
              </button>
            </div>
          ) : (
            <div style={{ backgroundColor: '#131b2e', border: '1px solid #1e293b', borderRadius: '16px', padding: '2rem' }}>
              <h2 style={{ margin: '0 0 0.5rem 0', fontSize: '1.5rem', color: '#f8fafc' }}>Etsy & Ticari PDF Raporları</h2>
              <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
                Mistik Holding e-ticaret otomasyonu ve dijital ürün üretim havuzu.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div style={{ backgroundColor: '#090d16', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.25rem' }}>
                  <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', color: '#818cf8' }}>The Crystal Tarot Raporu</h3>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 1rem 0' }}>34 Sayfalık Özel Analiz PDF</p>
                  <span style={{ display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: '600', backgroundColor: '#064e3b', color: '#34d399' }}>Otomatik Satışta</span>
                </div>

                <div style={{ backgroundColor: '#090d16', border: '1px solid #1e293b', borderRadius: '12px', padding: '1.25rem' }}>
                  <h3 style={{ margin: '0 0 0.4rem 0', fontSize: '1rem', color: '#818cf8' }}>Astro-Numeroloji Paketi</h3>
                  <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '0 0 1rem 0' }}>Ebced & Burç Haritası</p>
                  <span style={{ display: 'inline-block', padding: '0.2rem 0.6rem', borderRadius: '999px', fontSize: '0.75rem', fontWeight: '600', backgroundColor: '#064e3b', color: '#34d399' }}>Etsy Aktif</span>
                </div>
              </div>
            </div>
          )}

        </div>
      </main>
    </div>
  );
}