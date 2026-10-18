# Sample inventory

All people, organizations, and figures in this sample are fictional.

Everything here is fictional: the person, the employers, the figures. It exists so you can try CardFile
and run the tests without any real career data.

- `inventory/` has four role files covering every evidence level and one excluded bullet.
- `sample_source.txt` is the made-up resume text the imported bullets came from.

```
python3 scripts/build_resume.py hlb-01 hlb-02 bwc-01 ccp-01 --inventory sample/inventory
python3 scripts/check_source.py sample/sample_source.txt --inventory sample/inventory
```
