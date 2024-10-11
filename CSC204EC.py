'''
Extra Credit 1 - Custom Sorting Task

Name: Kevin Gawrinauth
Hofstra ID: 

'''

import random
import time
import matplotlib.pyplot as visualizer # type: ignore

def my_sort_algo(array_to_sort):
    '''
    Implementing my custom algorithm for sorting numbers in an ascending order
    '''
    num_elems = len(array_to_sort)
    for idx in range(1, num_elems):
        temp_value = array_to_sort[idx]
        position = idx - 1
        '''' I will now shift the elements if they're greater than the current one '''
        while position >= 0 and array_to_sort[position] > temp_value:
            array_to_sort[position + 1] = array_to_sort[position]
            position -= 1
        ''' Place temp_value in its correct spot '''
        array_to_sort[position + 1] = temp_value
    return array_to_sort 

def mygenerated_plotgraph():
    '''
    Will now set the graph comparing the running times for different cases of sorting.
    '''
    sizes = [100, 500, 1000, 2000, 5000]
    sorted_case_time = []
    reversed_case_time = []
    random_case_time = []

    for size in sizes:
        ''' This is the best case of the array sorted below '''
        sorted_case = list(range(size))
        start_time = time.perf_counter()
        my_sort_algo(sorted_case)  # Corrected function call
        sorted_case_time.append((time.perf_counter() - start_time) * 1e6)

        ''' This is the worse case of the array in reverse order below '''
        reversed_case = list(range(size, 0, -1))
        start_time = time.perf_counter()
        my_sort_algo(reversed_case)  # Corrected function call
        reversed_case_time.append((time.perf_counter() - start_time) * 1e6)

        ''' This is the average case set in random order below'''
        random_case = random.sample(range(size), size)
        start_time = time.perf_counter()
        my_sort_algo(random_case)  # Corrected function call
        random_case_time.append((time.perf_counter() - start_time) * 1e6)

    '''Lastly im setting the plots for all the parts of the graph to be displayed and outputted'''
    visualizer.plot(sizes, sorted_case_time, label='Best Case - Sorted')
    visualizer.plot(sizes, reversed_case_time, label='Worst Case - Reversed')
    visualizer.plot(sizes, random_case_time, label='Average Case - Random')

    visualizer.xlabel('Input Size (n)')
    visualizer.ylabel('Time (microseconds)')
    visualizer.title('Performance of Sorting Algorithm')
    visualizer.legend()
    visualizer.show()


if __name__ == '__main__':
    mygenerated_plotgraph()  # Corrected function call
