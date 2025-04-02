![image](https://github.com/user-attachments/assets/b65ccb95-dc19-4f18-9abb-db4598d330c4)# Графический редактор

## Лабораторная работа №1

### Тема
Генерация отрезков.

### Задание:
Разработать элементарный графический редактор, реализующий построение отрезков с
помощью алгоритма ЦДА, целочисленного алгоритм Брезенхема и алгоритма Ву. Вызов
способа генерации отрезка задается выбором. В редакторе кроме режима генерации отрезков в пользовательском окне должен
быть предусмотрен отладочный режим, где отображается пошаговое решение на дискретной сетке. 

### Алгоритмы
#### Алгоритм ЦДА
Алгоритм DDA-линии растеризует отрезок прямой между двумя заданными точками, используя вычисления с вещественными числами. 
Аббревиатура DDA в названии этого алгоритма машинной графики происходит от англ. 
Digital Differential Analyzer (цифровой дифференциальный анализатор) — вычислительное устройство, применявшееся ранее для генерации векторов. 
Несмотря на то, что сейчас этот алгоритм практически не применяется, он позволяет понять сложности, которые встречаются при растеризации отрезка и способы их решения.

#### Алгоритм Брезенхема
Алгоритм Брезенхема (англ. Bresenham's line algorithm) — это алгоритм, определяющий, какие точки двумерного растра нужно закрасить, 
чтобы получить близкое приближение прямой линии между двумя заданными точками.

#### Алгоритм Ву Сяолиня
Алгоритм использует механизмы сглаживания при растеризации линии. При этом ступенчатые выступы на линии становятся менее заметны.

### Интерфейс

![image](https://github.com/user-attachments/assets/490ea6eb-94a8-44ea-a21d-0156e344a2e1)

### Технологии
Python\
Tkinter

### Вывод
В результате реализации графического редактора, использующего алгоритмы построения отрезков (ЦДА, Брезенхема и Ву), 
реализована отрисовка отрезков с режимом отладки.
