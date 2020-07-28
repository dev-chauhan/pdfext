find falsified -iname "*.pdf" | while read f
do
    python main.py "$f" 1
done
