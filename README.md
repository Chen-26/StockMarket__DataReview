# �г����̿���

��ɫ��Ӧʽ A �� / ���ɸ�����ҳ����ֱ�Ӵ� `index.html` ���鲼�ֺͽ����������ļ�ģʽ��ʾ����Ԥ�����ݡ����� Cloudflare Pages ��ҳ���ͨ��ͬ�� Pages Function ��ȡ���顣

## ҳ������

- A �ɡ����ɷ���չʾ��Ҫָ���ʹ�����ġ�
- ����/����������ÿ������ɸѡȫ����ָ������ɡ�
- ÿ���г��жϡ����׸��̺���һ���ƻ��Զ������ڵ�ǰ�������
- ��ҳÿ���Ӽ�����飻Function ʹ�ñ�Ե���棬�����ظ�����

## Cloudflare Pages ��Ѳ���

1. �� Cloudflare ����̨���� **Workers & Pages �� Create application �� Pages �� Connect to Git**��
2. ��Ȩ GitHub��ѡ��˽�вֿ� `Chen-26/StockMarket__DataReview` ��������֧ `main`��
3. Framework preset ѡ **None**��Build command �� `mkdir -p public && cp index.html public/index.html`��Build output directory �� `public`��
4. ���沢�����Ժ� push �� `main` ���Զ�������

`functions/api/quotes.js` �� Pages Function������ API key ������ʱ����������Cloudflare Pages Functions �����ռ�� Workers Free ���������ȣ���̬��Դ������ѡ�Git ������ѷ���ÿ����� 500 �ι������������� Cloudflare ��ǰ�ײ�˵��Ϊ׼��

> ע�⣺Cloudflare Pages ��ַĬ�Ͽɹ������ʣ�˽�� GitHub �ֿⲻ���Զ�����ҳҲ���˽�С����̱ʼ�ֻ�浱ǰ������������ϴ�������Ҫ��ҳ���ʿ��ƣ�����Ϊվ������ Cloudflare Access��

## ������ע�б�

�� `functions/api/quotes.js` �� `WATCHLIST` �޸Ĵ��룻��������ģ����� `index.html` ����չʾ���ƺͷ��ࡣ

## ���Ľ���ð�̲���

��Ҫ Node.js 20 ����°汾������ĿĿ¼ִ�� `node tests/smoke.cjs`����֤ҳ��ű���A ��/����������Ⱦ�����ɸѡ���������ʼ��Զ�����/��ա��ֶ�ˢ�¡�����Ԥ�����˺����� Function ��Ӧ��

## ����˵��

�������� Yahoo Finance ͼ���ӿڡ��ýӿڲ�����ʵʱ SLA �Ĺ������� API�������ӳ١���������ʱ�����ã�ҳ��������̲ο���������Ͷ�ʽ��顣

