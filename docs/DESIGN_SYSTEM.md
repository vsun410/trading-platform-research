# 🎨 Design System Reference

**Design System:** Kinetic Minimalism  
**Master Location:** [storage/docs/DESIGN_SYSTEM.md](https://github.com/vsun410/trading-platform-storage/blob/main/docs/DESIGN_SYSTEM.md)

> ⚠️ 이 문서는 요약본입니다. 전체 디자인 시스템은 **storage 레포**를 참조하세요.

---

## Research 레포 UI 역할

| 기능 | 설명 |
|------|------|
| 백테스트 대시보드 | 전략 성과 시각화 |
| 김프 모니터링 | 실시간 김프율 차트 |
| 신호 로그 | 생성된 신호 히스토리 |

---

## 핵심 디자인 토큰 (Quick Reference)

### 색상

```css
/* 중립 */
--bg-primary: #FFFFFF;
--bg-secondary: #F8F9FA;
--text-primary: #0A0A0B;
--text-secondary: #5F6368;

/* 액센트 */
--accent-primary: #0066FF;
--color-long: #00D4AA;    /* 상승/수익 */
--color-short: #FF3366;   /* 하락/손실 */
```

### 그림자 (방향성: 우하단)

```css
--shadow-md: 4px 8px 16px rgba(0, 0, 0, 0.08);
--shadow-long: 4px 8px 24px rgba(0, 212, 170, 0.20);
--shadow-short: 4px 8px 24px rgba(255, 51, 102, 0.20);
```

### 방향성 요소 (필수)

```css
/* 카드 하단 액센트 바 */
.accent-bar::after {
  content: '';
  position: absolute;
  left: 24px;
  bottom: 0;
  width: 60px;
  height: 4px;
  background: var(--accent-primary);
  transform: skewX(-20deg);
}
```

---

## Research UI 컴포넌트

### 1. 백테스트 성과 카드

```tsx
<div className="
  relative bg-white rounded-xl p-6
  shadow-[4px_8px_16px_rgba(0,0,0,0.08)]
">
  {/* Diagonal corner */}
  <div className="absolute top-0 right-0 w-20 h-20 
    bg-gradient-to-bl from-[#E6F0FF] to-transparent"
    style={{ clipPath: 'polygon(100% 0, 100% 100%, 0 0)' }}
  />
  
  <p className="text-sm text-[#5F6368]">Total Return</p>
  <p className="text-3xl font-bold font-mono text-[#00D4AA]">+24.5%</p>
  
  {/* Bottom accent */}
  <div className="absolute bottom-0 left-6 w-16 h-1 bg-[#0066FF] -skew-x-12" />
</div>
```

### 2. 김프율 디스플레이

```tsx
<div className="
  flex items-center gap-4 p-4
  bg-white rounded-lg
  shadow-[4px_8px_16px_rgba(0,212,170,0.15)]
  border-l-4 border-[#00D4AA]
">
  <div>
    <p className="text-xs text-[#9AA0A6] uppercase tracking-wider">김프율</p>
    <p className="text-2xl font-mono font-bold text-[#00D4AA]">+3.24%</p>
  </div>
  
  {/* Motion streak */}
  <div className="w-8 h-0.5 bg-gradient-to-r from-[#00D4AA] to-transparent" />
</div>
```

---

## 체크리스트

- [ ] 방향성 요소 1개 이상 포함
- [ ] 그림자 단일 방향 (우하단)
- [ ] 색상: 중립 90% + 액센트 10%
- [ ] 글래스/뉴모피즘 요소 없음
- [ ] 숫자는 Monospace 폰트

---

*전체 가이드: [storage/docs/DESIGN_SYSTEM.md](https://github.com/vsun410/trading-platform-storage/blob/main/docs/DESIGN_SYSTEM.md)*
